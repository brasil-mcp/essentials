import json
from pathlib import Path

import pytest

from brasil_mcp.core.validators.cpf import validate_cpf

_FIXTURES = json.loads((Path(__file__).parents[2] / "fixtures/validators/cpf.json").read_text())


@pytest.mark.parametrize("cpf", _FIXTURES["valid"])
def test_valid_cpf(cpf: str):
    result = validate_cpf(cpf)
    assert result.valid is True
    assert result.error is None
    assert result.formatted is not None
    assert len(result.formatted.replace(".", "").replace("-", "")) == 11


@pytest.mark.parametrize("case", _FIXTURES["invalid"])
def test_invalid_cpf(case: dict):
    result = validate_cpf(case["input"])
    assert result.valid is False
    assert result.error is not None
    assert str(result.error.code) == case["code"]


def test_formatted_idempotent():
    r1 = validate_cpf("52998224725")
    assert r1.valid
    assert r1.formatted is not None
    r2 = validate_cpf(r1.formatted)
    assert r2.valid
