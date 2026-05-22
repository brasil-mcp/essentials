"""Tests for lookup_cep — ViaCEP integration."""

from __future__ import annotations

from unittest.mock import patch

import httpx

from brasil_mcp.core.lookups import cep as cep_mod
from brasil_mcp.core.lookups.cep import lookup_cep


def _viacep_response(payload):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    return handler


def _http_error_handler(status: int):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status)

    return handler


def test_invalid_empty():
    r = lookup_cep("")
    assert r["valid"] is False
    assert r["error"]["code"] == "EMPTY_INPUT"


def test_invalid_short():
    r = lookup_cep("123")
    assert r["valid"] is False
    assert r["error"]["code"] == "INVALID_LENGTH"


def test_invalid_long():
    r = lookup_cep("123456789012")
    assert r["valid"] is False
    assert r["error"]["code"] == "INVALID_LENGTH"


def test_success(mock_transport_factory):
    payload = {
        "cep": "01310-200",
        "logradouro": "Avenida Paulista",
        "complemento": "lado par",
        "bairro": "Bela Vista",
        "localidade": "São Paulo",
        "uf": "SP",
        "ibge": "3550308",
        "ddd": "11",
    }
    with patch.object(cep_mod, "get_json", side_effect=lambda *a, **k: payload):
        r = lookup_cep("01310-200")
    assert r["valid"] is True
    assert r["cep"] == "01310200"
    assert r["logradouro"] == "Avenida Paulista"
    assert r["uf"] == "SP"
    assert r["ibge"] == "3550308"
    assert r["error"] is None


def test_viacep_signals_not_found():
    with patch.object(cep_mod, "get_json", side_effect=lambda *a, **k: {"erro": True}):
        r = lookup_cep("99999999")
    assert r["valid"] is False
    assert r["error"]["code"] == "NOT_FOUND"


def test_viacep_404():
    from brasil_mcp.core.lookups.http_client import NotFoundError

    with patch.object(cep_mod, "get_json", side_effect=NotFoundError("x")):
        r = lookup_cep("99999999")
    assert r["error"]["code"] == "NOT_FOUND"


def test_network_failure():
    from brasil_mcp.core.lookups.http_client import NetworkError

    with patch.object(cep_mod, "get_json", side_effect=NetworkError("timeout")):
        r = lookup_cep("01310200")
    assert r["error"]["code"] == "NETWORK_ERROR"


def test_caches_result():
    payload = {"cep": "01310-200", "logradouro": "Av", "localidade": "SP", "uf": "SP"}
    call_count = {"n": 0}

    def fake(*a, **k):
        call_count["n"] += 1
        return payload

    with patch.object(cep_mod, "get_json", side_effect=fake):
        r1 = lookup_cep("01310200")
        r2 = lookup_cep("01310-200")  # same digits, different mask

    assert call_count["n"] == 1  # second call hit cache
    assert r1 == r2
