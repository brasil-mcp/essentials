"""Tests for lookup_ddd."""

from __future__ import annotations

from unittest.mock import patch

from brasil_mcp.core.lookups import ddd as ddd_mod
from brasil_mcp.core.lookups.ddd import lookup_ddd


def test_empty():
    r = lookup_ddd("")
    assert r["error"]["code"] == "EMPTY_INPUT"


def test_wrong_length():
    r = lookup_ddd("1")
    assert r["error"]["code"] == "INVALID_LENGTH"


def test_success_int_input():
    payload = {"state": "SP", "cities": ["SAO PAULO", "OSASCO"]}
    with patch.object(ddd_mod, "get_json", side_effect=lambda *a, **k: payload):
        r = lookup_ddd(11)
    assert r["valid"] is True
    assert r["ddd"] == "11"
    assert r["uf"] == "SP"
    assert "SAO PAULO" in r["cidades"]


def test_alternate_field_names():
    """BrasilAPI sometimes returns 'uf'/'cidades' instead of 'state'/'cities'."""
    payload = {"uf": "RJ", "cidades": ["RIO DE JANEIRO"]}
    with patch.object(ddd_mod, "get_json", side_effect=lambda *a, **k: payload):
        r = lookup_ddd("21")
    assert r["uf"] == "RJ"
    assert r["cidades"] == ["RIO DE JANEIRO"]


def test_not_found():
    from brasil_mcp.core.lookups.http_client import NotFoundError

    with patch.object(ddd_mod, "get_json", side_effect=NotFoundError("x")):
        r = lookup_ddd("99")
    assert r["error"]["code"] == "NOT_FOUND"


def test_network():
    from brasil_mcp.core.lookups.http_client import NetworkError

    with patch.object(ddd_mod, "get_json", side_effect=NetworkError("x")):
        r = lookup_ddd("11")
    assert r["error"]["code"] == "NETWORK_ERROR"


def test_empty_cities_in_response():
    with patch.object(ddd_mod, "get_json", side_effect=lambda *a, **k: {"state": "AC"}):
        r = lookup_ddd("68")
    assert r["valid"] is True
    assert r["cidades"] == []


def test_caches_result():
    n = {"c": 0}

    def fake(*a, **k):
        n["c"] += 1
        return {"state": "SP", "cities": ["X"]}

    with patch.object(ddd_mod, "get_json", side_effect=fake):
        lookup_ddd("11")
        lookup_ddd("11")
    assert n["c"] == 1
