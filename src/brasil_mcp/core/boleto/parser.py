"""Parser único de boletos brasileiros (FEBRABAN).

Aceita três formatos de entrada:

* Linha digitável bancária — 47 dígitos
* Código de barras bancário — 44 dígitos
* Linha digitável de arrecadação (concessionária/tributo) — 48 dígitos

Detecção automática: se o primeiro dígito é ``8`` → arrecadação; caso
contrário, bancário. Caracteres não-dígitos (espaços, pontos, hifens)
são aceitos e ignorados.
"""

from __future__ import annotations

import json
import re
from datetime import date, timedelta
from importlib import resources
from typing import Any

from brasil_mcp.core.boleto.linha_digitavel import (
    barcode_to_linha_bancario,
    dv_mod10,
    dv_mod11_bancario,
    is_arrecadacao,
    linha_to_barcode_bancario,
    normalize,
)
from brasil_mcp.core.errors import ErrorCode, ErrorObj
from brasil_mcp.core.models import ValidationResult

# Caracteres permitidos no input cru (dígitos, separadores comuns e espaço).
_ALLOWED_CHARS_RE = re.compile(r"[^\d.\-\s/]")

# Fator de vencimento — bases FEBRABAN
_FATOR_BASE_OLD = date(1997, 10, 7)  # fator 1000
_FATOR_RESET_BOUNDARY = date(2025, 2, 21)  # último dia com base antiga
_FATOR_BASE_NEW = date(2025, 2, 22)  # fator 1000 (pós-reset)

_SEGMENTO_ARRECADACAO_MAP: dict[str, str] = {
    "1": "tributo_municipal",
    "2": "concessionaria_agua_saneamento",
    "3": "concessionaria_eletrica",
    "4": "concessionaria_telefonia",
    "5": "tributo_federal",
    "6": "carnes_assemelhados",
    "7": "multas_transito",
    "8": "tributo_estadual",
    "9": "outros",
}


# ---------------------------------------------------------------------------
# FEBRABAN bank table — bundled JSON
# ---------------------------------------------------------------------------


def _load_febraban_codes() -> dict[str, dict[str, str]]:
    raw = resources.files("brasil_mcp.core.boleto").joinpath("febraban_codes.json").read_text(
        encoding="utf-8"
    )
    return json.loads(raw)


_FEBRABAN_CODES: dict[str, dict[str, str]] = _load_febraban_codes()


def _lookup_banco(codigo: str) -> dict[str, str] | None:
    entry = _FEBRABAN_CODES.get(codigo)
    if entry is None:
        return None
    return {
        "codigo_febraban": codigo,
        "ispb": entry["ispb"],
        "nome": entry["nome"],
    }


# ---------------------------------------------------------------------------
# Decodificadores
# ---------------------------------------------------------------------------


def _decode_fator_vencimento(fator: int) -> date | None:
    """Decodifica fator de vencimento em data.

    Heurística para o reset FEBRABAN de 2025-02-22:
    * Calcula candidato com base antiga (1997-10-07).
    * Se ``candidato <= 2025-02-21`` → retorna candidato.
    * Caso contrário, calcula com base nova (2025-02-22).

    ``fator == 0`` → ``None`` (boleto sem vencimento).
    """
    if fator <= 0:
        return None
    candidate_old = _FATOR_BASE_OLD + timedelta(days=fator - 1000)
    if candidate_old <= _FATOR_RESET_BOUNDARY:
        return candidate_old
    return _FATOR_BASE_NEW + timedelta(days=fator - 1000)


# ---------------------------------------------------------------------------
# Validação comum
# ---------------------------------------------------------------------------


def _empty_input_error(raw: str) -> ValidationResult:
    return ValidationResult(
        valid=False,
        raw=raw,
        error=ErrorObj(
            ErrorCode.EMPTY_INPUT,
            "Boleto não pode ser vazio.",
            "Boleto cannot be empty.",
        ),
    )


def _invalid_character_error(raw: str) -> ValidationResult:
    return ValidationResult(
        valid=False,
        raw=raw,
        error=ErrorObj(
            ErrorCode.INVALID_CHARACTER,
            "Boleto deve conter apenas dígitos e separadores opcionais (espaço, ponto, hífen).",
            "Boleto must contain only digits and optional separators (space, dot, hyphen).",
        ),
    )


def _invalid_length_error(raw: str, got: int) -> ValidationResult:
    return ValidationResult(
        valid=False,
        raw=raw,
        error=ErrorObj(
            ErrorCode.INVALID_LENGTH,
            (
                f"Boleto deve ter 44 (código de barras bancário), 47 (linha digitável bancária) "
                f"ou 48 (arrecadação) dígitos; recebido {got}."
            ),
            (
                f"Boleto must have 44 (bank barcode), 47 (bank linha digitável) "
                f"or 48 (arrecadação) digits; received {got}."
            ),
            suggestion="Verifique se o número não está truncado ou colado com lixo.",
        ),
    )


def _invalid_checksum_error(raw: str, detail_pt: str, detail_en: str) -> ValidationResult:
    return ValidationResult(
        valid=False,
        raw=raw,
        error=ErrorObj(
            ErrorCode.INVALID_CHECKSUM,
            f"Dígito verificador inválido: {detail_pt}.",
            f"Invalid checksum digit: {detail_en}.",
        ),
    )


# ---------------------------------------------------------------------------
# Bancário
# ---------------------------------------------------------------------------


def _parse_bancario_from_linha(raw: str, linha47: str) -> ValidationResult:
    # Verifica DVs dos 3 campos (mod 10).
    campo1 = linha47[0:9]  # banco_moeda(4) + campo1_data(5)
    dv1_actual = int(linha47[9])
    if dv_mod10(campo1) != dv1_actual:
        return _invalid_checksum_error(
            raw,
            "DV do campo 1 não confere",
            "field 1 DV mismatch",
        )

    campo2_data = linha47[10:20]
    dv2_actual = int(linha47[20])
    if dv_mod10(campo2_data) != dv2_actual:
        return _invalid_checksum_error(
            raw,
            "DV do campo 2 não confere",
            "field 2 DV mismatch",
        )

    campo3_data = linha47[21:31]
    dv3_actual = int(linha47[31])
    if dv_mod10(campo3_data) != dv3_actual:
        return _invalid_checksum_error(
            raw,
            "DV do campo 3 não confere",
            "field 3 DV mismatch",
        )

    # Converte para barcode (44) e valida o DV geral (mod 11).
    barcode = linha_to_barcode_bancario(linha47)
    return _validate_and_build_bancario(raw, linha47, barcode)


def _parse_bancario_from_barcode(raw: str, barcode44: str) -> ValidationResult:
    # Reconstrói linha digitável a partir do barcode (recalcula DVs dos campos).
    linha47 = barcode_to_linha_bancario(barcode44)
    return _validate_and_build_bancario(raw, linha47, barcode44)


def _validate_and_build_bancario(
    raw: str, linha47: str, barcode44: str
) -> ValidationResult:
    # DV geral = barcode[4]; demais 43 dígitos formam o pacote para mod 11.
    dv_geral_actual = int(barcode44[4])
    pacote = barcode44[0:4] + barcode44[5:]
    dv_geral_calc = dv_mod11_bancario(pacote)
    if dv_geral_calc != dv_geral_actual:
        return _invalid_checksum_error(
            raw,
            "DV geral (módulo 11) não confere",
            "general DV (mod 11) mismatch",
        )

    codigo_banco = barcode44[0:3]
    banco = _lookup_banco(codigo_banco)
    fator = int(barcode44[5:9])
    valor_cents = int(barcode44[9:19])
    nosso_numero = barcode44[19:44]  # 25 dígitos — campo livre por banco

    vencimento_date = _decode_fator_vencimento(fator)

    extras: dict[str, Any] = {
        "tipo": "bancario",
        "linha_digitavel": linha47,
        "codigo_barras": barcode44,
        "banco": banco,
        "moeda": "BRL",
        "valor": valor_cents if valor_cents > 0 else None,
        "vencimento": vencimento_date.isoformat() if vencimento_date else None,
        "fator_vencimento": fator if fator > 0 else None,
        "nosso_numero": nosso_numero,
        "segmento_arrecadacao": None,
    }
    return ValidationResult(
        valid=True,
        raw=raw,
        formatted=linha47,
        extras=extras,
    )


# ---------------------------------------------------------------------------
# Arrecadação
# ---------------------------------------------------------------------------


def _parse_arrecadacao(raw: str, digits: str) -> ValidationResult:
    # ``digits`` tem 48 dígitos (linha digitável). A linha digitável de
    # arrecadação é formada por 4 blocos de 12 dígitos onde o último de
    # cada bloco é o DV do bloco (mod 10 ou mod 11 conforme identificador
    # de valor).
    #
    # Mapeamento LD ↔ código de barras (44 dígitos):
    #   barcode[0:11]   = LD[0:11]
    #   LD[11]          = DV do bloco 1 (não vai pro barcode)
    #   barcode[11:22]  = LD[12:23]
    #   LD[23]          = DV do bloco 2
    #   barcode[22:33]  = LD[24:35]
    #   LD[35]          = DV do bloco 3
    #   barcode[33:44]  = LD[36:47]
    #   LD[47]          = DV do bloco 4
    identificador_valor = digits[2]
    # mod10 quando identificador é "6" ou "7"; mod11 quando "8" ou "9".
    use_mod11 = identificador_valor in ("8", "9")

    for i in range(4):
        bloco = digits[i * 12 : (i + 1) * 12]
        bloco_data = bloco[:11]
        dv_actual = int(bloco[11])
        dv_calc = dv_mod11_bancario(bloco_data) if use_mod11 else dv_mod10(bloco_data)
        if dv_calc != dv_actual:
            return _invalid_checksum_error(
                raw,
                f"DV do bloco {i + 1} (arrecadação) não confere",
                f"arrecadação block {i + 1} DV mismatch",
            )

    # Reconstrói código de barras (44 dígitos) removendo os 4 DVs de bloco.
    # NOTE (v0.1.0): retornamos esse barcode como cortesia ao chamador, mas
    # NÃO validamos o DV geral do barcode contra os outros 43 dígitos —
    # a especificação completa de arrecadação será revisitada numa versão
    # futura. O que importa nesta versão: aceitar input em qualquer forma
    # e devolver ambos os campos coerentes.
    codigo_barras = "".join(digits[i * 12 : i * 12 + 11] for i in range(4))

    # Segmento (barcode[1] == LD[1]).
    segmento_codigo = codigo_barras[1]
    segmento = _SEGMENTO_ARRECADACAO_MAP.get(segmento_codigo, "outros")

    # Valor: barcode[4:15] (11 dígitos), após "8" (0), segmento (1),
    # identificador (2) e DV geral (3). Quando identificador é 6/7, o valor
    # está em centavos; quando 8/9, é referenciado/quantidade (None).
    valor_cents: int | None
    if identificador_valor in ("6", "7"):
        valor_raw = int(codigo_barras[4:15])
        valor_cents = valor_raw if valor_raw > 0 else None
    else:
        valor_cents = None

    extras: dict[str, Any] = {
        "tipo": "arrecadacao",
        "linha_digitavel": digits,
        "codigo_barras": codigo_barras,
        "banco": None,
        "moeda": "BRL",
        "valor": valor_cents,
        "vencimento": None,
        "fator_vencimento": None,
        "nosso_numero": None,
        "segmento_arrecadacao": segmento,
    }
    return ValidationResult(
        valid=True,
        raw=raw,
        formatted=digits,
        extras=extras,
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def parse_boleto(value: str) -> ValidationResult:
    """Parser único de boletos brasileiros (FEBRABAN)."""
    raw = value or ""
    if not raw.strip():
        return _empty_input_error(raw)

    if _ALLOWED_CHARS_RE.search(raw):
        return _invalid_character_error(raw)

    digits = normalize(raw)

    if is_arrecadacao(digits):
        if len(digits) != 48:
            return _invalid_length_error(raw, len(digits))
        return _parse_arrecadacao(raw, digits)

    if len(digits) == 47:
        return _parse_bancario_from_linha(raw, digits)
    if len(digits) == 44:
        return _parse_bancario_from_barcode(raw, digits)

    return _invalid_length_error(raw, len(digits))
