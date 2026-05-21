import json
from pathlib import Path

import pytest

from brasil_mcp.core.validators.renavam import validate_renavam

_FIXTURES = json.loads((Path(__file__).parents[2] / "fixtures/validators/renavam.json").read_text())


@pytest.mark.parametrize("renavam", _FIXTURES["valid"])
def test_valid_renavam(renavam: str):
    result = validate_renavam(renavam)
    assert result.valid is True
    assert result.error is None
    assert result.formatted is not None
    assert len(result.formatted) == 11
    assert result.formatted.isdigit()


@pytest.mark.parametrize("case", _FIXTURES["invalid"])
def test_invalid_renavam(case: dict):
    result = validate_renavam(case["input"])
    assert result.valid is False
    assert result.error is not None
    assert str(result.error.code) == case["code"]


def test_formatted_idempotent():
    r1 = validate_renavam("12345678900")
    assert r1.valid
    assert r1.formatted is not None
    r2 = validate_renavam(r1.formatted)
    assert r2.valid


def test_accepts_short_9_digit():
    # 9-digit RENAVAM (legacy) must be accepted and padded to 11.
    r = validate_renavam("234567899")
    assert r.valid is True
    assert r.formatted == "00234567899"


def test_accepts_10_digit():
    r = validate_renavam("1234567897")
    assert r.valid is True
    assert r.formatted == "01234567897"
