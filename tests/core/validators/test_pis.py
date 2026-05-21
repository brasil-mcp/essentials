import json
from pathlib import Path

import pytest

from brasil_mcp.core.validators.pis import validate_pis

_FIXTURES = json.loads(
    (Path(__file__).parents[2] / "fixtures/validators/pis.json").read_text()
)


@pytest.mark.parametrize("pis", _FIXTURES["valid"])
def test_valid_pis(pis: str):
    result = validate_pis(pis)
    assert result.valid is True
    assert result.error is None
    assert result.formatted is not None
    assert len(result.formatted.replace(".", "").replace("-", "")) == 11


@pytest.mark.parametrize("case", _FIXTURES["invalid"])
def test_invalid_pis(case: dict):
    result = validate_pis(case["input"])
    assert result.valid is False
    assert result.error is not None
    assert str(result.error.code) == case["code"]


def test_formatted_idempotent():
    r1 = validate_pis("12067890125")
    assert r1.valid
    assert r1.formatted is not None
    r2 = validate_pis(r1.formatted)
    assert r2.valid
