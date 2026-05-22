"""Tests for the 5 lookup tool wrappers (MCP + CLI)."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from brasil_mcp.adapters.cli.app import app
from brasil_mcp.adapters.mcp.server import build_server


@pytest.fixture(autouse=True)
def isolated_cache(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    yield


def _unwrap(result):
    if isinstance(result, tuple) and len(result) == 2:
        return result[1]
    return result


# ---------- MCP tool wrappers ----------


@pytest.mark.asyncio
async def test_mcp_lookup_cep(monkeypatch):
    payload = {"cep": "01310-200", "logradouro": "Av Paulista", "localidade": "SP", "uf": "SP"}
    with patch("brasil_mcp.core.lookups.cep.get_json", return_value=payload):
        server = build_server()
        result = await server.call_tool("lookup_cep", {"cep": "01310200"})
    data = _unwrap(result)
    assert data["valid"] is True
    assert data["cep"] == "01310200"


@pytest.mark.asyncio
async def test_mcp_lookup_banco(monkeypatch):
    payload = {"code": 341, "ispb": "60701190", "name": "Itaú"}
    with patch("brasil_mcp.core.lookups.banco.get_json", return_value=payload):
        server = build_server()
        result = await server.call_tool("lookup_banco_febraban", {"codigo": "341"})
    data = _unwrap(result)
    assert data["valid"] is True
    assert data["codigo_febraban"] == "341"


@pytest.mark.asyncio
async def test_mcp_lookup_ddd(monkeypatch):
    payload = {"state": "SP", "cities": ["SAO PAULO"]}
    with patch("brasil_mcp.core.lookups.ddd.get_json", return_value=payload):
        server = build_server()
        result = await server.call_tool("lookup_ddd", {"ddd": "11"})
    data = _unwrap(result)
    assert data["valid"] is True
    assert data["uf"] == "SP"


@pytest.mark.asyncio
async def test_mcp_lookup_ibge(monkeypatch):
    payload = [{"id": 3550308, "nome": "São Paulo"}]
    with patch("brasil_mcp.core.lookups.ibge.get_json", return_value=payload):
        server = build_server()
        result = await server.call_tool("lookup_ibge_municipio", {"nome": "São Paulo", "uf": "SP"})
    data = _unwrap(result)
    assert data["valid"] is True
    assert data["ibge_code"] == "3550308"


@pytest.mark.asyncio
async def test_mcp_lookup_cotacao(monkeypatch):
    payload = {
        "value": [
            {
                "cotacaoCompra": 5.5,
                "cotacaoVenda": 5.51,
                "dataHoraCotacao": "2026-05-20 13:00:00.000",
            }
        ]
    }
    with patch("brasil_mcp.core.lookups.cotacao.get_json", return_value=payload):
        server = build_server()
        result = await server.call_tool("lookup_cotacao_brl", {"moeda": "USD"})
    data = _unwrap(result)
    assert data["valid"] is True
    assert data["moeda"] == "USD"


# ---------- CLI subcommands ----------


def test_cli_lookup_cep():
    payload = {"cep": "01310-200", "logradouro": "Av", "localidade": "SP", "uf": "SP"}
    with patch("brasil_mcp.core.lookups.cep.get_json", return_value=payload):
        runner = CliRunner()
        result = runner.invoke(app, ["lookup-cep", "01310200"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["valid"] is True


def test_cli_lookup_banco():
    payload = {"code": 341, "name": "Itaú"}
    with patch("brasil_mcp.core.lookups.banco.get_json", return_value=payload):
        runner = CliRunner()
        result = runner.invoke(app, ["lookup-banco-febraban", "341"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["valid"] is True


def test_cli_lookup_ddd():
    payload = {"state": "SP", "cities": ["A"]}
    with patch("brasil_mcp.core.lookups.ddd.get_json", return_value=payload):
        runner = CliRunner()
        result = runner.invoke(app, ["lookup-ddd", "11"])
    assert result.exit_code == 0


def test_cli_lookup_ibge():
    payload = [{"id": 3550308, "nome": "São Paulo"}]
    with patch("brasil_mcp.core.lookups.ibge.get_json", return_value=payload):
        runner = CliRunner()
        result = runner.invoke(app, ["lookup-ibge-municipio", "São Paulo", "--uf", "SP"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["valid"] is True


def test_cli_lookup_cotacao():
    payload = {
        "value": [
            {"cotacaoCompra": 5.5, "cotacaoVenda": 5.51, "dataHoraCotacao": "2026-05-20 13:00:00.0"}
        ]
    }
    with patch("brasil_mcp.core.lookups.cotacao.get_json", return_value=payload):
        runner = CliRunner()
        result = runner.invoke(app, ["lookup-cotacao-brl", "USD"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["valid"] is True


# ---------- v0.3.0: endereco_cep, validate_telefone, whatsapp_qr ----------


@pytest.mark.asyncio
async def test_mcp_lookup_endereco_cep():
    payload = [
        {"cep": "01310-200", "logradouro": "Av", "localidade": "SP", "uf": "SP"}
    ]
    with patch("brasil_mcp.core.lookups.cep.get_json", return_value=payload):
        server = build_server()
        result = await server.call_tool(
            "lookup_endereco_cep",
            {"uf": "SP", "cidade": "São Paulo", "logradouro": "Avenida Paulista"},
        )
    data = _unwrap(result)
    assert data["valid"] is True
    assert data["count"] == 1


@pytest.mark.asyncio
async def test_mcp_validate_telefone():
    server = build_server()
    result = await server.call_tool("validate_telefone", {"value": "11987654321"})
    data = _unwrap(result)
    assert data["valid"] is True
    assert data["tipo"] == "celular"


@pytest.mark.asyncio
async def test_mcp_generate_whatsapp_qr():
    server = build_server()
    result = await server.call_tool(
        "generate_whatsapp_qr",
        {"telefone": "11987654321", "mensagem": "oi"},
    )
    data = _unwrap(result)
    assert data["valid"] is True
    assert "wa.me/5511987654321" in data["url"]


def test_cli_validate_telefone():
    runner = CliRunner()
    result = runner.invoke(app, ["validate-telefone", "11987654321"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["valid"] is True


def test_cli_lookup_endereco_cep():
    payload = [{"cep": "01310-200", "logradouro": "Av", "localidade": "SP", "uf": "SP"}]
    with patch("brasil_mcp.core.lookups.cep.get_json", return_value=payload):
        runner = CliRunner()
        result = runner.invoke(
            app,
            ["lookup-endereco-cep", "SP", "São Paulo", "Avenida Paulista"],
        )
    assert result.exit_code == 0


def test_cli_generate_whatsapp_qr():
    runner = CliRunner()
    result = runner.invoke(
        app,
        ["generate-whatsapp-qr", "11987654321", "--mensagem", "olá"],
    )
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["valid"] is True
