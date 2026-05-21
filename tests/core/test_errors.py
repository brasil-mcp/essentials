from brasil_mcp.core.errors import ErrorCode, ErrorObj


def test_error_code_is_string():
    assert str(ErrorCode.INVALID_FORMAT) == "INVALID_FORMAT"


def test_error_obj_to_dict_includes_all_fields():
    err = ErrorObj(
        code=ErrorCode.INVALID_LENGTH,
        message_pt="CPF deve ter 11 dígitos",
        message_en="CPF must have 11 digits",
        suggestion="Verifique o tamanho",
    )
    assert err.to_dict() == {
        "code": "INVALID_LENGTH",
        "message_pt": "CPF deve ter 11 dígitos",
        "message_en": "CPF must have 11 digits",
        "suggestion": "Verifique o tamanho",
    }


def test_error_obj_suggestion_optional():
    err = ErrorObj(code=ErrorCode.EMPTY_INPUT, message_pt="vazio", message_en="empty")
    assert err.to_dict()["suggestion"] is None
