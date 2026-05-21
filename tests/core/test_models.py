from brasil_mcp.core.errors import ErrorCode, ErrorObj
from brasil_mcp.core.models import ValidationResult


def test_validation_result_valid():
    r = ValidationResult(valid=True, raw="123", formatted="1-2-3")
    assert r.to_dict() == {"valid": True, "formatted": "1-2-3", "raw": "123", "error": None}


def test_validation_result_with_error():
    err = ErrorObj(ErrorCode.INVALID_CHECKSUM, "checksum", "checksum")
    r = ValidationResult(valid=False, raw="999", error=err)
    d = r.to_dict()
    assert d["valid"] is False
    assert d["error"]["code"] == "INVALID_CHECKSUM"


def test_validation_result_extras_merged():
    r = ValidationResult(valid=True, raw="x", extras={"format": "legacy"})
    assert r.to_dict()["format"] == "legacy"
