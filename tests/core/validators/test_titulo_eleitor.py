import json
from pathlib import Path

import pytest

from brasil_mcp.core.validators.titulo_eleitor import validate_titulo_eleitor

_FIXTURES = json.loads(
    (Path(__file__).parents[2] / "fixtures/validators/titulo_eleitor.json").read_text()
)


@pytest.mark.parametrize("case", _FIXTURES["valid"])
def test_valid_titulo(case: dict):
    result = validate_titulo_eleitor(case["input"])
    assert result.valid is True
    assert result.error is None
    assert result.formatted is not None
    assert len(result.formatted) == 12
    assert result.extras.get("uf") == case["uf"]


@pytest.mark.parametrize("case", _FIXTURES["invalid"])
def test_invalid_titulo(case: dict):
    result = validate_titulo_eleitor(case["input"])
    assert result.valid is False
    assert result.error is not None
    assert str(result.error.code) == case["code"]


def test_formatted_idempotent():
    r1 = validate_titulo_eleitor("123456780191")
    assert r1.valid
    assert r1.formatted is not None
    r2 = validate_titulo_eleitor(r1.formatted)
    assert r2.valid
    assert r2.extras.get("uf") == "SP"


def test_sp_mg_exception():
    # Case where DV1 mod-11 returns 10 → exception collapses to 1 for SP.
    r = validate_titulo_eleitor("000000060116")
    assert r.valid is True
    assert r.extras["uf"] == "SP"


def test_exterior_uf():
    r = validate_titulo_eleitor("998877662828")
    assert r.valid is True
    assert r.extras["uf"] == "Exterior"
