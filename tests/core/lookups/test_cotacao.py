"""Tests for lookup_cotacao_brl — BCB PTAX."""

from __future__ import annotations

from unittest.mock import patch

from brasil_mcp.core.lookups import cotacao as cotacao_mod
from brasil_mcp.core.lookups.cotacao import lookup_cotacao_brl

PTAX_USD = {
    "value": [
        {
            "cotacaoCompra": 5.4321,
            "cotacaoVenda": 5.4350,
            "dataHoraCotacao": "2026-05-20 13:09:42.345",
        }
    ]
}


def test_empty_moeda():
    r = lookup_cotacao_brl("")
    assert r["error"]["code"] == "EMPTY_INPUT"


def test_unsupported_currency():
    r = lookup_cotacao_brl("XYZ")
    assert r["error"]["code"] == "UNSUPPORTED_FORMAT"


def test_invalid_date_format():
    r = lookup_cotacao_brl("USD", data_cotacao="not-a-date")
    assert r["error"]["code"] == "INVALID_DATE"


def test_success_historical():
    with patch.object(cotacao_mod, "get_json", side_effect=lambda *a, **k: PTAX_USD):
        r = lookup_cotacao_brl("USD", data_cotacao="2026-05-20")
    assert r["valid"] is True
    assert r["moeda"] == "USD"
    assert r["compra_cents"] == 543  # round(5.4321 * 100)
    assert r["venda_cents"] == 544
    assert r["compra"] == "5.4321"
    assert r["fonte"] == "BCB PTAX"


def test_success_today_default():
    with patch.object(cotacao_mod, "get_json", side_effect=lambda *a, **k: PTAX_USD):
        r = lookup_cotacao_brl("USD")
    assert r["valid"] is True


def test_no_quote_available():
    with patch.object(cotacao_mod, "get_json", side_effect=lambda *a, **k: {"value": []}):
        r = lookup_cotacao_brl("USD", data_cotacao="2026-05-20")
    assert r["error"]["code"] == "NOT_FOUND"


def test_network_failure():
    from brasil_mcp.core.lookups.http_client import NetworkError

    with patch.object(cotacao_mod, "get_json", side_effect=NetworkError("x")):
        r = lookup_cotacao_brl("USD")
    assert r["error"]["code"] == "NETWORK_ERROR"


def test_case_insensitive_moeda():
    with patch.object(cotacao_mod, "get_json", side_effect=lambda *a, **k: PTAX_USD):
        r = lookup_cotacao_brl("usd")
    assert r["moeda"] == "USD"


def test_caches_historical_aggressive():
    """A date > 2 days old is cached for a year — second call doesn't hit network."""
    n = {"c": 0}

    def fake(*a, **k):
        n["c"] += 1
        return PTAX_USD

    with patch.object(cotacao_mod, "get_json", side_effect=fake):
        lookup_cotacao_brl("USD", data_cotacao="2024-01-15")
        lookup_cotacao_brl("USD", data_cotacao="2024-01-15")
    assert n["c"] == 1


def test_supported_currencies_list():
    """All supported currencies route to PTAX without error code."""
    for moeda in ["USD", "EUR", "GBP", "JPY", "ARS", "CHF", "CAD", "AUD"]:
        with patch.object(cotacao_mod, "get_json", side_effect=lambda *a, **k: PTAX_USD):
            r = lookup_cotacao_brl(moeda)
        assert r["valid"] is True
        assert r["moeda"] == moeda
