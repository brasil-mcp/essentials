"""Tests for lookup_endereco_cep (ViaCEP reverse)."""

from __future__ import annotations

from unittest.mock import patch

from brasil_mcp.core.lookups import cep as cep_mod
from brasil_mcp.core.lookups.cep import lookup_endereco_cep


def test_required_fields():
    r = lookup_endereco_cep("", "São Paulo", "Av Paulista")
    assert r["valid"] is False
    assert r["error"]["code"] == "EMPTY_INPUT"


def test_uf_length():
    r = lookup_endereco_cep("X", "São Paulo", "Av Paulista")
    assert r["error"]["code"] == "INVALID_LENGTH"


def test_short_logradouro():
    r = lookup_endereco_cep("SP", "São Paulo", "Av")
    assert r["error"]["code"] == "INVALID_LENGTH"


def test_short_cidade():
    r = lookup_endereco_cep("SP", "SP", "Av Paulista")
    assert r["error"]["code"] == "INVALID_LENGTH"


def test_success():
    payload = [
        {
            "cep": "01310-200",
            "logradouro": "Avenida Paulista",
            "complemento": "lado par",
            "bairro": "Bela Vista",
            "localidade": "São Paulo",
            "uf": "SP",
            "ibge": "3550308",
            "ddd": "11",
        }
    ]
    with patch.object(cep_mod, "get_json", side_effect=lambda *a, **k: payload):
        r = lookup_endereco_cep("SP", "São Paulo", "Avenida Paulista")
    assert r["valid"] is True
    assert r["count"] == 1
    assert r["matches"][0]["cep"] == "01310200"
    assert r["matches"][0]["bairro"] == "Bela Vista"


def test_empty_list_means_not_found():
    with patch.object(cep_mod, "get_json", side_effect=lambda *a, **k: []):
        r = lookup_endereco_cep("SP", "Inexistente", "Rua X")
    assert r["valid"] is False
    assert r["error"]["code"] == "NOT_FOUND"


def test_dict_erro_means_not_found():
    """ViaCEP às vezes responde com {'erro': true} em vez de lista vazia."""
    with patch.object(cep_mod, "get_json", side_effect=lambda *a, **k: {"erro": True}):
        r = lookup_endereco_cep("SP", "Inexistente", "Rua X")
    assert r["error"]["code"] == "NOT_FOUND"


def test_not_found_via_http_404():
    from brasil_mcp.core.lookups.http_client import NotFoundError

    with patch.object(cep_mod, "get_json", side_effect=NotFoundError("x")):
        r = lookup_endereco_cep("SP", "São Paulo", "Av Paulista")
    assert r["error"]["code"] == "NOT_FOUND"


def test_network_error():
    from brasil_mcp.core.lookups.http_client import NetworkError

    with patch.object(cep_mod, "get_json", side_effect=NetworkError("timeout")):
        r = lookup_endereco_cep("SP", "São Paulo", "Av Paulista")
    assert r["error"]["code"] == "NETWORK_ERROR"


def test_caches_result():
    payload = [{"cep": "01310-200", "logradouro": "Av", "localidade": "SP", "uf": "SP"}]
    n = {"c": 0}

    def fake(*a, **k):
        n["c"] += 1
        return payload

    with patch.object(cep_mod, "get_json", side_effect=fake):
        lookup_endereco_cep("SP", "São Paulo", "Av Paulista")
        lookup_endereco_cep("sp", "são paulo", "av paulista")  # case-insensitive cache key
    assert n["c"] == 1


def test_strips_dash_from_cep_in_response():
    payload = [{"cep": "01310-200", "logradouro": "Av", "localidade": "SP", "uf": "SP"}]
    with patch.object(cep_mod, "get_json", side_effect=lambda *a, **k: payload):
        r = lookup_endereco_cep("SP", "São Paulo", "Avenida Paulista")
    assert r["matches"][0]["cep"] == "01310200"
