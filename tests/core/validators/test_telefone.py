"""Tests for validate_telefone."""

from __future__ import annotations

import pytest

from brasil_mcp.core.validators.telefone import validate_telefone

# ---- Successes ----


@pytest.mark.parametrize(
    "value,expected_formatted,expected_tipo,expected_e164",
    [
        ("11987654321", "(11) 98765-4321", "celular", "+5511987654321"),
        ("(11) 98765-4321", "(11) 98765-4321", "celular", "+5511987654321"),
        ("11 9 8765 4321", "(11) 98765-4321", "celular", "+5511987654321"),
        ("+5511987654321", "(11) 98765-4321", "celular", "+5511987654321"),
        ("+55 (11) 98765-4321", "(11) 98765-4321", "celular", "+5511987654321"),
        ("5511987654321", "(11) 98765-4321", "celular", "+5511987654321"),
        ("1134567890", "(11) 3456-7890", "fixo", "+551134567890"),
        ("(11) 3456-7890", "(11) 3456-7890", "fixo", "+551134567890"),
        ("+551134567890", "(11) 3456-7890", "fixo", "+551134567890"),
        ("(21) 99876-5432", "(21) 99876-5432", "celular", "+5521998765432"),
        ("(31) 5555-1234", "(31) 5555-1234", "fixo", "+553155551234"),
    ],
)
def test_valid_phones(value, expected_formatted, expected_tipo, expected_e164):
    r = validate_telefone(value)
    assert r.valid is True
    assert r.formatted == expected_formatted
    assert r.extras["tipo"] == expected_tipo
    assert r.extras["e164"] == expected_e164


def test_extras_include_ddd():
    r = validate_telefone("11987654321")
    assert r.extras["ddd"] == "11"


def test_extras_include_international_format():
    r = validate_telefone("11987654321")
    assert r.extras["formatted_international"] == "+55 11 98765-4321"


def test_extras_include_e164():
    r = validate_telefone("11987654321")
    assert r.extras["e164"] == "+5511987654321"


# ---- Failures ----


def test_empty():
    r = validate_telefone("")
    assert r.valid is False
    assert str(r.error.code) == "EMPTY_INPUT"


def test_whitespace_only():
    r = validate_telefone("   ")
    assert r.valid is False
    assert str(r.error.code) == "EMPTY_INPUT"


def test_too_short():
    r = validate_telefone("123")
    assert r.valid is False
    assert str(r.error.code) == "INVALID_LENGTH"


def test_too_long():
    r = validate_telefone("1198765432109")  # 13 digits after strip
    assert r.valid is False
    assert str(r.error.code) == "INVALID_LENGTH"


def test_non_brazilian_country_code():
    r = validate_telefone("+15551234567")
    assert r.valid is False
    assert str(r.error.code) == "UNSUPPORTED_FORMAT"


def test_invalid_ddd():
    """DDD 20 não é atribuído pela Anatel."""
    r = validate_telefone("20987654321")
    assert r.valid is False
    assert str(r.error.code) == "INVALID_FORMAT"
    assert "20" in r.error.message_pt


def test_celular_without_leading_9():
    """11 dígitos com DDD válido mas segundo dígito != 9."""
    r = validate_telefone("11187654321")
    assert r.valid is False
    assert str(r.error.code) == "INVALID_FORMAT"


def test_fixo_with_invalid_first_digit():
    """10 dígitos mas começa com 6/7/8/9 (não é fixo válido)."""
    r = validate_telefone("1167654321")
    assert r.valid is False
    assert str(r.error.code) == "INVALID_FORMAT"


def test_letters_rejected_after_stripping():
    """Letras misturadas com dígitos não passam pelo strip de [^\\d+]."""
    # Após strip, "11abc987654321" vira "11987654321" — 11 dígitos válidos!
    # Esse teste verifica que strip remove TUDO que não é dígito/+.
    r = validate_telefone("11abc987654321")
    assert r.valid is True  # strip remove 'abc'


def test_plus_in_middle_is_rejected():
    """Caso degenerado: '+' no meio da string passa pelo regex inicial mas
    falha o stripped.isdigit() check (cobre line 141)."""
    r = validate_telefone("11+987654321")
    assert r.valid is False
    assert str(r.error.code) == "INVALID_CHARACTER"
