"""End-to-end tests para parse_boleto (bancário e arrecadação)."""

from __future__ import annotations

from datetime import date, timedelta

from brasil_mcp.core.boleto.linha_digitavel import (
    dv_mod10,
    dv_mod11_bancario,
    linha_to_barcode_bancario,
)
from brasil_mcp.core.boleto.parser import (
    _FATOR_BASE_NEW,
    _FATOR_BASE_OLD,
    _FATOR_RESET_BOUNDARY,
    _decode_fator_vencimento,
    parse_boleto,
)

# ---------------------------------------------------------------------------
# Builders sintéticos (vetores são montados aritmeticamente — zero PII).
# ---------------------------------------------------------------------------


def _build_linha47(
    banco: str = "341",
    moeda: str = "9",
    fator: str = "9876",
    valor: str = "0000012345",
    campo1_data: str = "12345",
    campo2_data: str = "1234567890",
    campo3_data: str = "0987654321",
) -> str:
    """Monta uma linha digitável bancária 47-dígitos com todos os DVs corretos."""
    banco_moeda = banco + moeda
    dv1 = dv_mod10(banco_moeda + campo1_data)
    dv2 = dv_mod10(campo2_data)
    dv3 = dv_mod10(campo3_data)
    # DV geral mod 11 sobre os 43 dígitos do barcode (todos menos o próprio
    # DV na posição 4): banco_moeda + fator + valor + campo1_data + campo2_data + campo3_data.
    pacote = banco_moeda + fator + valor + campo1_data + campo2_data + campo3_data
    dv_geral = dv_mod11_bancario(pacote)
    return (
        f"{banco_moeda}{campo1_data}{dv1}"
        f"{campo2_data}{dv2}"
        f"{campo3_data}{dv3}"
        f"{dv_geral}{fator}{valor}"
    )


def _build_arrecadacao48(
    segmento: str = "3",
    identificador: str = "6",
    dv_geral: str = "0",
    valor: str = "00001234500",  # 11 dígitos
    dados_livres: str = "0" * 29,  # 29 dígitos
) -> str:
    """Monta linha digitável de arrecadação 48-dígitos com DVs de bloco corretos.

    Layout do barcode interno (44 dígitos):
        [0]   "8"
        [1]   segmento
        [2]   identificador de valor
        [3]   dv geral (placeholder — não validamos nesta versão)
        [4:15] valor (11)
        [15:44] dados livres (29)
    """
    assert len(valor) == 11
    assert len(dados_livres) == 29
    barcode = f"8{segmento}{identificador}{dv_geral}{valor}{dados_livres}"
    assert len(barcode) == 44

    use_mod11 = identificador in ("8", "9")

    # Particiona em 4 blocos de 11 dígitos de dados.
    blocks = [
        barcode[0:11],
        barcode[11:22],
        barcode[22:33],
        barcode[33:44],
    ]
    out = []
    for b in blocks:
        dv = dv_mod11_bancario(b) if use_mod11 else dv_mod10(b)
        out.append(f"{b}{dv}")
    linha = "".join(out)
    assert len(linha) == 48
    return linha


# ---------------------------------------------------------------------------
# Empty / character / length
# ---------------------------------------------------------------------------


def test_empty_input():
    r = parse_boleto("")
    assert r.valid is False
    assert r.error is not None
    assert str(r.error.code) == "EMPTY_INPUT"


def test_whitespace_only_input():
    r = parse_boleto("    ")
    assert r.valid is False
    assert r.error is not None
    assert str(r.error.code) == "EMPTY_INPUT"


def test_invalid_character():
    r = parse_boleto("3419x12345" + "1234567890" + "0" * 28)
    assert r.valid is False
    assert r.error is not None
    assert str(r.error.code) == "INVALID_CHARACTER"


def test_invalid_length_too_short():
    r = parse_boleto("123")
    assert r.valid is False
    assert r.error is not None
    assert str(r.error.code) == "INVALID_LENGTH"


def test_invalid_length_too_long_bancario():
    # 46 dígitos — não bate com nenhum formato suportado (não bancário, não arrecadação).
    r = parse_boleto("3" + "0" * 45)
    assert r.valid is False
    assert r.error is not None
    assert str(r.error.code) == "INVALID_LENGTH"


def test_arrecadacao_wrong_length():
    # Começa com 8 mas tem 47 chars.
    r = parse_boleto("8" + "0" * 46)
    assert r.valid is False
    assert r.error is not None
    assert str(r.error.code) == "INVALID_LENGTH"


# ---------------------------------------------------------------------------
# Bancário — valid happy path
# ---------------------------------------------------------------------------


def test_bancario_valid_basic():
    linha = _build_linha47(banco="341", fator="9876", valor="0000012345")
    r = parse_boleto(linha)
    assert r.valid is True, r.error
    assert r.error is None
    assert r.extras["tipo"] == "bancario"
    assert r.extras["linha_digitavel"] == linha
    assert len(r.extras["codigo_barras"]) == 44
    assert r.extras["banco"]["codigo_febraban"] == "341"
    assert r.extras["banco"]["nome"] == "Itaú Unibanco S.A."
    assert r.extras["banco"]["ispb"] == "60701190"
    assert r.extras["moeda"] == "BRL"
    assert r.extras["valor"] == 12345
    assert r.extras["fator_vencimento"] == 9876
    assert r.extras["vencimento"] is not None
    assert r.extras["nosso_numero"] is not None
    assert len(r.extras["nosso_numero"]) == 25
    assert r.extras["segmento_arrecadacao"] is None


def test_bancario_accepts_whitespace_and_punctuation():
    linha = _build_linha47(banco="237")
    # Insere espaços e pontos como costuma vir colado de site de banco.
    masked = f"{linha[0:5]}.{linha[5:10]} {linha[10:16]}.{linha[16:21]} {linha[21:27]}.{linha[27:32]} {linha[32]}  {linha[33:]}"
    r = parse_boleto(masked)
    assert r.valid is True, r.error
    assert r.extras["banco"]["codigo_febraban"] == "237"


def test_bancario_accepts_44_digit_barcode():
    linha = _build_linha47(banco="104", valor="0000099900")
    barcode = linha_to_barcode_bancario(linha)
    r = parse_boleto(barcode)
    assert r.valid is True, r.error
    assert r.extras["tipo"] == "bancario"
    assert r.extras["codigo_barras"] == barcode
    assert r.extras["linha_digitavel"] == linha
    assert r.extras["banco"]["codigo_febraban"] == "104"
    assert r.extras["valor"] == 99900


def test_bancario_unknown_banco_returns_none():
    # Código de banco "999" não está na tabela.
    linha = _build_linha47(banco="999")
    r = parse_boleto(linha)
    assert r.valid is True, r.error
    assert r.extras["banco"] is None


def test_bancario_zero_valor():
    linha = _build_linha47(valor="0000000000")
    r = parse_boleto(linha)
    assert r.valid is True
    assert r.extras["valor"] is None


def test_bancario_zero_fator_no_vencimento():
    linha = _build_linha47(fator="0000")
    r = parse_boleto(linha)
    assert r.valid is True
    assert r.extras["vencimento"] is None
    assert r.extras["fator_vencimento"] is None


# ---------------------------------------------------------------------------
# Bancário — checksum errors
# ---------------------------------------------------------------------------


def test_bancario_bad_campo1_dv():
    linha = list(_build_linha47())
    # Corrompe o DV do campo 1 (posição 9).
    linha[9] = "9" if linha[9] != "9" else "0"
    r = parse_boleto("".join(linha))
    assert r.valid is False
    assert r.error is not None
    assert str(r.error.code) == "INVALID_CHECKSUM"


def test_bancario_bad_campo2_dv():
    linha = list(_build_linha47())
    linha[20] = "9" if linha[20] != "9" else "0"
    r = parse_boleto("".join(linha))
    assert r.valid is False
    assert r.error is not None
    assert str(r.error.code) == "INVALID_CHECKSUM"


def test_bancario_bad_campo3_dv():
    linha = list(_build_linha47())
    linha[31] = "9" if linha[31] != "9" else "0"
    r = parse_boleto("".join(linha))
    assert r.valid is False
    assert r.error is not None
    assert str(r.error.code) == "INVALID_CHECKSUM"


def test_bancario_bad_general_dv():
    # Constrói linha com DVs de campo válidos mas DV geral inválido.
    # Estratégia: pega linha válida e troca apenas o DV geral (pos 32) por
    # outro dígito qualquer que não bate.
    linha = _build_linha47()
    original_dv = linha[32]
    other = "1" if original_dv != "1" else "2"
    bad = linha[:32] + other + linha[33:]
    r = parse_boleto(bad)
    assert r.valid is False
    assert r.error is not None
    assert str(r.error.code) == "INVALID_CHECKSUM"


def test_bancario_44_barcode_bad_general_dv():
    linha = _build_linha47()
    barcode = list(linha_to_barcode_bancario(linha))
    barcode[4] = "1" if barcode[4] != "1" else "2"
    r = parse_boleto("".join(barcode))
    assert r.valid is False
    assert r.error is not None
    assert str(r.error.code) == "INVALID_CHECKSUM"


# ---------------------------------------------------------------------------
# Fator de vencimento — FEBRABAN reset heuristic
# ---------------------------------------------------------------------------


def _fator_for_date_old_base(target: date) -> int:
    return 1000 + (target - _FATOR_BASE_OLD).days


def test_fator_1000_maps_to_old_base():
    fator = 1000
    target = _FATOR_BASE_OLD
    linha = _build_linha47(fator=f"{fator:04d}")
    r = parse_boleto(linha)
    assert r.valid is True
    assert r.extras["vencimento"] == target.isoformat()


def test_fator_1001_maps_to_old_base_plus_one():
    linha = _build_linha47(fator="1001")
    r = parse_boleto(linha)
    assert r.valid is True
    assert r.extras["vencimento"] == (_FATOR_BASE_OLD + timedelta(days=1)).isoformat()


def test_fator_at_reset_boundary_uses_old_base():
    """Heurística: fator cujo candidato com base antiga = boundary → usa base antiga.

    Sob a base antiga 1997-10-07, mapear 2025-02-21 exige fator > 9999
    (fora do range 4-dígitos da linha digitável). Testamos o decoder
    diretamente porque a aritmética é o que importa para a heurística.
    """
    fator = _fator_for_date_old_base(_FATOR_RESET_BOUNDARY)
    decoded = _decode_fator_vencimento(fator)
    assert decoded == _FATOR_RESET_BOUNDARY


def test_fator_after_reset_uses_new_base():
    """Heurística: fator cujo candidato antigo > 2025-02-21 → usa base nova."""
    boundary_fator = _fator_for_date_old_base(_FATOR_RESET_BOUNDARY)
    fator = boundary_fator + 1  # candidato antigo = 2025-02-22 (> boundary)
    decoded = _decode_fator_vencimento(fator)
    expected = _FATOR_BASE_NEW + timedelta(days=fator - 1000)
    assert decoded == expected


def test_fator_zero_returns_none():
    assert _decode_fator_vencimento(0) is None


# ---------------------------------------------------------------------------
# Arrecadação
# ---------------------------------------------------------------------------


def test_arrecadacao_valid_segmento_eletrica_mod10():
    linha = _build_arrecadacao48(segmento="3", identificador="6", valor="00001234500")
    r = parse_boleto(linha)
    assert r.valid is True, r.error
    assert r.extras["tipo"] == "arrecadacao"
    assert r.extras["segmento_arrecadacao"] == "concessionaria_eletrica"
    assert r.extras["valor"] == 1234500
    assert r.extras["banco"] is None
    assert r.extras["vencimento"] is None
    assert r.extras["fator_vencimento"] is None
    assert r.extras["nosso_numero"] is None
    assert r.extras["linha_digitavel"] == linha
    assert len(r.extras["codigo_barras"]) == 44


def test_arrecadacao_valid_segmento_water_mod10():
    linha = _build_arrecadacao48(segmento="2", identificador="6")
    r = parse_boleto(linha)
    assert r.valid is True, r.error
    assert r.extras["segmento_arrecadacao"] == "concessionaria_agua_saneamento"


def test_arrecadacao_identificador_8_uses_mod11_and_no_valor():
    linha = _build_arrecadacao48(segmento="1", identificador="8", valor="00000099900")
    r = parse_boleto(linha)
    assert r.valid is True, r.error
    assert r.extras["segmento_arrecadacao"] == "tributo_municipal"
    # Identificador 8 = valor referenciado → não devolvemos cents.
    assert r.extras["valor"] is None


def test_arrecadacao_zero_valor():
    linha = _build_arrecadacao48(valor="00000000000")
    r = parse_boleto(linha)
    assert r.valid is True
    assert r.extras["valor"] is None


def test_arrecadacao_bad_block_dv():
    linha = list(_build_arrecadacao48())
    # Corrompe DV do bloco 1 (posição 11).
    linha[11] = "9" if linha[11] != "9" else "0"
    r = parse_boleto("".join(linha))
    assert r.valid is False
    assert r.error is not None
    assert str(r.error.code) == "INVALID_CHECKSUM"


def test_arrecadacao_accepts_whitespace():
    linha = _build_arrecadacao48(segmento="3")
    spaced = f"{linha[0:12]} {linha[12:24]} {linha[24:36]} {linha[36:48]}"
    r = parse_boleto(spaced)
    assert r.valid is True, r.error
    assert r.extras["tipo"] == "arrecadacao"
