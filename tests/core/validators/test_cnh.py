import json
from pathlib import Path

import pytest

from brasil_mcp.core.validators.cnh import validate_cnh

_FIXTURES = json.loads((Path(__file__).parents[2] / "fixtures/validators/cnh.json").read_text())


@pytest.mark.parametrize("cnh", _FIXTURES["valid"])
def test_valid_cnh(cnh: str):
    result = validate_cnh(cnh)
    assert result.valid is True
    assert result.error is None
    assert result.formatted is not None
    assert len(result.formatted) == 11
    assert result.formatted.isdigit()


@pytest.mark.parametrize("case", _FIXTURES["invalid"])
def test_invalid_cnh(case: dict):
    result = validate_cnh(case["input"])
    assert result.valid is False
    assert result.error is not None
    assert str(result.error.code) == case["code"]


def test_formatted_idempotent():
    r1 = validate_cnh("12345678900")
    assert r1.valid
    assert r1.formatted is not None
    r2 = validate_cnh(r1.formatted)
    assert r2.valid
