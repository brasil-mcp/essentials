"""Tests for lookup_banco_febraban."""

from __future__ import annotations

from unittest.mock import patch

from brasil_mcp.core.lookups import banco as banco_mod
from brasil_mcp.core.lookups.banco import lookup_banco_febraban


def test_empty():
    r = lookup_banco_febraban("")
    assert r["valid"] is False
    assert r["error"]["code"] == "EMPTY_INPUT"


def test_too_long():
    r = lookup_banco_febraban("12345")
    assert r["valid"] is False
    assert r["error"]["code"] == "INVALID_LENGTH"


def test_success():
    payload = {"code": 341, "ispb": "60701190", "name": "Itaú", "fullName": "Itaú Unibanco S.A."}
    with patch.object(banco_mod, "get_json", side_effect=lambda *a, **k: payload):
        r = lookup_banco_febraban("341")
    assert r["valid"] is True
    assert r["codigo_febraban"] == "341"
    assert r["nome"] == "Itaú"
    assert r["ispb"] == "60701190"


def test_zero_pad():
    payload = {"code": 1, "ispb": "00000000", "name": "BB"}
    with patch.object(banco_mod, "get_json", side_effect=lambda *a, **k: payload):
        r = lookup_banco_febraban("1")
    assert r["valid"] is True
    # input "1" → padded to "001"
    assert r["codigo_febraban"] == "001"


def test_not_found():
    from brasil_mcp.core.lookups.http_client import NotFoundError

    with patch.object(banco_mod, "get_json", side_effect=NotFoundError("x")):
        r = lookup_banco_febraban("999")
    assert r["error"]["code"] == "NOT_FOUND"


def test_network():
    from brasil_mcp.core.lookups.http_client import NetworkError

    with patch.object(banco_mod, "get_json", side_effect=NetworkError("x")):
        r = lookup_banco_febraban("341")
    assert r["error"]["code"] == "NETWORK_ERROR"


def test_caches_result():
    payload = {"code": 341, "ispb": "60701190", "name": "Itaú"}
    n = {"c": 0}

    def fake(*a, **k):
        n["c"] += 1
        return payload

    with patch.object(banco_mod, "get_json", side_effect=fake):
        lookup_banco_febraban("341")
        lookup_banco_febraban("341")
    assert n["c"] == 1
