import json
from pathlib import Path

import pytest

from brasil_mcp.core.validators.cnpj import W1, W2, calc_digit, validate_cnpj

_FIXTURES = json.loads(
    (Path(__file__).parents[2] / "fixtures/validators/cnpj.json").read_text()
)


def _gen_valid_alphanum(base12: str) -> str:
    d1 = calc_digit(base12, W1)
    d2 = calc_digit(base12 + str(d1), W2)
    return base12 + str(d1) + str(d2)


@pytest.mark.parametrize("cnpj", _FIXTURES["valid_legacy"])
def test_valid_legacy(cnpj: str):
    r = validate_cnpj(cnpj)
    assert r.valid is True, r.error
    assert r.extras["format"] == "legacy"


def test_valid_alphanumeric_generated():
    """Generate valid alphanumeric CNPJs and verify roundtrip."""
    for base12 in ["12ABC345001D", "BR1234567890", "AAAA1234BBBB", "X9Y8Z7654321"]:
        valid_cnpj = _gen_valid_alphanum(base12)
        r = validate_cnpj(valid_cnpj)
        assert r.valid is True, (valid_cnpj, r.error)
        assert r.extras["format"] == "alphanumeric"


@pytest.mark.parametrize("case", _FIXTURES["invalid"])
def test_invalid(case: dict):
    r = validate_cnpj(case["input"])
    assert r.valid is False
    assert r.error is not None
    assert str(r.error.code) == case["code"]


def test_legacy_format_preserved_through_normalization():
    r = validate_cnpj("11222333000181")
    assert r.valid
    assert r.formatted == "11.222.333/0001-81"


def test_alphanumeric_format_preserved():
    valid_cnpj = _gen_valid_alphanum("12ABC345001D")
    r = validate_cnpj(valid_cnpj)
    assert r.valid
    assert r.extras["format"] == "alphanumeric"
    assert r.formatted is not None
