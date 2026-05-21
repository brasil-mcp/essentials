"""Tests para o adapter MCP (FastMCP)."""
from __future__ import annotations

import json

import pytest
from mcp.server.fastmcp import FastMCP

from brasil_mcp.adapters.mcp.server import build_server

EXPECTED_TOOLS = {
    "validate_cpf",
    "validate_cnpj",
    "validate_pis",
    "validate_renavam",
    "validate_cnh",
    "validate_titulo_eleitor",
    "validate_credit_card",
    "parse_boleto",
    "parse_pix_brcode",
    "generate_pix_brcode",
    "is_feriado_nacional",
    "proximo_dia_util",
    "contar_dias_uteis",
    "listar_feriados",
}


def test_build_server_returns_fastmcp() -> None:
    server = build_server()
    assert isinstance(server, FastMCP)


def test_server_registers_all_14_tools() -> None:
    server = build_server()
    tools = server._tool_manager.list_tools()
    names = {t.name for t in tools}
    assert len(tools) == 14, f"Esperava 14 tools, encontrei {len(tools)}: {names}"
    missing = EXPECTED_TOOLS - names
    assert not missing, f"Tools faltando: {missing}"


def test_each_tool_has_description() -> None:
    """Cada tool deve ter docstring/description (vira description visível ao LLM)."""
    server = build_server()
    tools = server._tool_manager.list_tools()
    for t in tools:
        assert t.description, f"Tool {t.name} sem description"


def _unwrap_call_tool(result: object) -> dict:
    """Extrai o dict estruturado do retorno de FastMCP.call_tool.

    O FastMCP retorna `(content_blocks, structured_data)` na versão atual; ou
    apenas `content_blocks` em versões antigas. Lidamos com ambos.
    """
    if isinstance(result, tuple) and len(result) == 2:
        content_blocks, structured = result
        if isinstance(structured, dict):
            return structured
        return json.loads(content_blocks[0].text)
    # fallback: assume lista de content blocks
    return json.loads(result[0].text)  # type: ignore[index, union-attr]


@pytest.mark.asyncio
async def test_call_validate_cpf_via_mcp() -> None:
    server = build_server()
    result = await server.call_tool("validate_cpf", {"value": "52998224725"})
    payload = _unwrap_call_tool(result)
    assert payload["valid"] is True
    assert payload["raw"] == "52998224725"


@pytest.mark.asyncio
async def test_call_is_feriado_nacional_via_mcp() -> None:
    server = build_server()
    result = await server.call_tool("is_feriado_nacional", {"date": "2026-09-07"})
    payload = _unwrap_call_tool(result)
    assert payload["is_feriado"] is True
