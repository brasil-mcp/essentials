"""Unit tests para os helpers de linha digitável / código de barras bancário."""

from __future__ import annotations

import pytest

from brasil_mcp.core.boleto.linha_digitavel import (
    barcode_to_linha_bancario,
    dv_mod10,
    dv_mod11_bancario,
    is_arrecadacao,
    linha_to_barcode_bancario,
    normalize,
)

# ---------------------------------------------------------------------------
# normalize
# ---------------------------------------------------------------------------


def test_normalize_strips_non_digits():
    assert normalize("12.345-67 89") == "123456789"


def test_normalize_handles_empty():
    assert normalize("") == ""
    assert normalize("   ") == ""


def test_normalize_none_safe():
    # type: ignore[arg-type] -- runtime safety
    assert normalize(None) == ""  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# is_arrecadacao
# ---------------------------------------------------------------------------


def test_is_arrecadacao_true():
    assert is_arrecadacao("812345") is True


def test_is_arrecadacao_false():
    assert is_arrecadacao("0001234") is False
    assert is_arrecadacao("3411234") is False


def test_is_arrecadacao_empty():
    assert is_arrecadacao("") is False


# ---------------------------------------------------------------------------
# dv_mod10
# ---------------------------------------------------------------------------


def test_dv_mod10_known_vector_12345():
    # Right-to-left: 5*2=10->1+0=1; 4*1=4; 3*2=6; 2*1=2; 1*2=2. sum=15. (10-15%10)%10 = 5.
    assert dv_mod10("12345") == 5


def test_dv_mod10_zero_string():
    assert dv_mod10("0000") == 0


def test_dv_mod10_single_digit_idempotent():
    # 7*2=14->1+4=5; (10-5)%10 = 5
    assert dv_mod10("7") == 5


def test_dv_mod10_produces_digit():
    for val in ("1", "99", "98765", "12345678901234"):
        d = dv_mod10(val)
        assert 0 <= d <= 9


# ---------------------------------------------------------------------------
# dv_mod11_bancario
# ---------------------------------------------------------------------------


def test_dv_mod11_known_vector():
    # Vector: "12345". Right-to-left with weights 2..9 cyclic:
    # 5*2=10; 4*3=12; 3*4=12; 2*5=10; 1*6=6. sum=50. 50%11 = 6. dv = 11-6 = 5.
    assert dv_mod11_bancario("12345") == 5


def test_dv_mod11_replaces_zero_ten_eleven_with_one():
    # All-zeros -> sum=0 -> dv calc = 11 -> mapped to 1.
    assert dv_mod11_bancario("0000") == 1


def test_dv_mod11_in_range():
    for val in ("1", "12", "1234", "999999999999", "100000000000"):
        d = dv_mod11_bancario(val)
        assert 1 <= d <= 9


# ---------------------------------------------------------------------------
# linha <-> barcode roundtrip
# ---------------------------------------------------------------------------


def _build_valid_linha47_for_test(
    banco: str = "341",
    moeda: str = "9",
    fator: str = "9876",
    valor: str = "0000012345",
    campo1_data: str = "12345",
    campo2_data: str = "1234567890",
    campo3_data: str = "0987654321",
) -> str:
    """Helper local: monta uma linha digitável bancária válida (DVs corretos)."""
    assert len(banco) == 3
    assert len(moeda) == 1
    assert len(fator) == 4
    assert len(valor) == 10
    assert len(campo1_data) == 5
    assert len(campo2_data) == 10
    assert len(campo3_data) == 10

    banco_moeda = banco + moeda

    # Compute campo DVs (mod10)
    dv1 = dv_mod10(banco_moeda + campo1_data)
    dv2 = dv_mod10(campo2_data)
    dv3 = dv_mod10(campo3_data)

    # DV geral mod 11 sobre os 43 dígitos do barcode (todos menos o próprio
    # DV na posição 4): banco_moeda + fator + valor + campo1 + campo2 + campo3.
    barcode_no_dv = banco_moeda + fator + valor + campo1_data + campo2_data + campo3_data
    dv_geral = dv_mod11_bancario(barcode_no_dv)

    return (
        f"{banco_moeda}{campo1_data}{dv1}"
        f"{campo2_data}{dv2}"
        f"{campo3_data}{dv3}"
        f"{dv_geral}{fator}{valor}"
    )


def test_linha_to_barcode_length():
    linha = _build_valid_linha47_for_test()
    barcode = linha_to_barcode_bancario(linha)
    assert len(barcode) == 44


def test_linha_to_barcode_roundtrip_identity():
    linha = _build_valid_linha47_for_test()
    barcode = linha_to_barcode_bancario(linha)
    rebuilt = barcode_to_linha_bancario(barcode)
    assert rebuilt == linha


def test_linha_to_barcode_roundtrip_multiple_vectors():
    vectors = [
        _build_valid_linha47_for_test(banco="001"),
        _build_valid_linha47_for_test(banco="237", fator="0000", valor="0000000000"),
        _build_valid_linha47_for_test(banco="104", valor="0000099900"),
        _build_valid_linha47_for_test(
            campo1_data="11111", campo2_data="2222222222", campo3_data="3333333333"
        ),
    ]
    for linha in vectors:
        barcode = linha_to_barcode_bancario(linha)
        assert barcode_to_linha_bancario(barcode) == linha


def test_linha_to_barcode_rejects_bad_length():
    with pytest.raises(ValueError):
        linha_to_barcode_bancario("12345")


def test_barcode_to_linha_rejects_bad_length():
    with pytest.raises(ValueError):
        barcode_to_linha_bancario("12345")
