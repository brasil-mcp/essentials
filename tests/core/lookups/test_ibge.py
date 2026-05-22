"""Tests for lookup_ibge_municipio."""

from __future__ import annotations

from unittest.mock import patch

from brasil_mcp.core.lookups import ibge as ibge_mod
from brasil_mcp.core.lookups.ibge import lookup_ibge_municipio

SP_MUNICIPIOS = [
    {"id": 3550308, "nome": "São Paulo"},
    {"id": 3548708, "nome": "Santos"},
    {"id": 3543907, "nome": "Ribeirão Preto"},
]

MG_MUNICIPIOS = [
    {"id": 3106200, "nome": "Belo Horizonte"},
    {"id": 3170701, "nome": "Uberaba"},
]


def _fake_get_json_factory(by_uf):
    def fake(url, **k):
        for uf, data in by_uf.items():
            if f"/{uf}/" in url:
                return data
        return []

    return fake


def test_empty_nome():
    r = lookup_ibge_municipio("")
    assert r["error"]["code"] == "EMPTY_INPUT"


def test_uf_specific_success():
    with patch.object(
        ibge_mod, "get_json", side_effect=_fake_get_json_factory({"SP": SP_MUNICIPIOS})
    ):
        r = lookup_ibge_municipio("São Paulo", uf="SP")
    assert r["valid"] is True
    assert r["uf"] == "SP"
    assert r["ibge_code"] == "3550308"
    assert r["nome"] == "São Paulo"


def test_uf_specific_with_accents_insensitive():
    with patch.object(
        ibge_mod, "get_json", side_effect=_fake_get_json_factory({"SP": SP_MUNICIPIOS})
    ):
        r = lookup_ibge_municipio("sao paulo", uf="SP")
    assert r["valid"] is True


def test_uf_specific_not_found():
    with patch.object(
        ibge_mod, "get_json", side_effect=_fake_get_json_factory({"SP": SP_MUNICIPIOS})
    ):
        r = lookup_ibge_municipio("Cidade Inexistente", uf="SP")
    assert r["valid"] is False
    assert r["error"]["code"] == "NOT_FOUND"


def test_uf_specific_network_failure():
    from brasil_mcp.core.lookups.http_client import NetworkError

    with patch.object(ibge_mod, "get_json", side_effect=NetworkError("x")):
        r = lookup_ibge_municipio("São Paulo", uf="SP")
    assert r["error"]["code"] == "NETWORK_ERROR"


def test_fan_out_all_ufs_when_uf_omitted():
    """When uf is None, library iterates over all 27 UFs."""
    by_uf = {"SP": SP_MUNICIPIOS, "MG": MG_MUNICIPIOS}
    # All other UFs return empty list (default in fake_get_json_factory)
    with patch.object(ibge_mod, "get_json", side_effect=_fake_get_json_factory(by_uf)):
        r = lookup_ibge_municipio("Santos")
    assert r["valid"] is True
    assert r["uf"] == "SP"
    assert r["ibge_code"] == "3548708"


def test_fan_out_network_error_short_circuits():
    """If any UF query fails, propagate the network error."""
    from brasil_mcp.core.lookups.http_client import NetworkError

    def fake(url, **k):
        if "/AC/" in url:
            raise NetworkError("x")
        return []

    with patch.object(ibge_mod, "get_json", side_effect=fake):
        r = lookup_ibge_municipio("Any City")
    assert r["error"]["code"] == "NETWORK_ERROR"


def test_caches_uf_response():
    """Same UF queried twice → one HTTP call."""
    n = {"c": 0}

    def fake(url, **k):
        n["c"] += 1
        return SP_MUNICIPIOS

    with patch.object(ibge_mod, "get_json", side_effect=fake):
        lookup_ibge_municipio("São Paulo", uf="SP")
        lookup_ibge_municipio("Santos", uf="SP")
    assert n["c"] == 1
