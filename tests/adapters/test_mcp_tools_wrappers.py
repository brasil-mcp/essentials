"""Smoke tests for every MCP tool wrapper registered in adapters/mcp/tools.py.

Each registered tool is exercised at least once (valid + invalid input where it
makes sense), via `server.call_tool(name, args)`. This drives every wrapper
body line to coverage.
"""

from __future__ import annotations

import json

import pytest

from brasil_mcp.adapters.mcp.server import build_server


def _unwrap(result: object) -> dict:
    """Extract the structured dict returned by FastMCP.call_tool.

    FastMCP returns `(content_blocks, structured)` in modern versions, or just
    `content_blocks` in older ones. Handle both.
    """
    if isinstance(result, tuple) and len(result) == 2:
        content_blocks, structured = result
        if isinstance(structured, dict):
            return structured
        return json.loads(content_blocks[0].text)
    return json.loads(result[0].text)  # type: ignore[index, union-attr]


# Each entry: (tool_name, valid_args, invalid_args). For tools that don't have
# a clean "invalid" path we just use a second valid call.
VALIDATOR_CASES: list[tuple[str, dict, dict]] = [
    ("validate_cpf", {"value": "52998224725"}, {"value": "00000000000"}),
    (
        "validate_cnpj",
        {"value": "11222333000181"},
        {"value": "00000000000000"},
    ),
    ("validate_pis", {"value": "12056412348"}, {"value": ""}),
    ("validate_renavam", {"value": "00482397500"}, {"value": "abc"}),
    ("validate_cnh", {"value": "04607277401"}, {"value": "1"}),
    ("validate_titulo_eleitor", {"value": "123456789012"}, {"value": ""}),
    (
        "validate_credit_card",
        {"value": "4111111111111111"},
        {"value": "0000000000000000"},
    ),
]


@pytest.mark.parametrize(("name", "valid", "invalid"), VALIDATOR_CASES)
@pytest.mark.asyncio
async def test_validator_tool_wrapper(name: str, valid: dict, invalid: dict) -> None:
    server = build_server()
    res_valid = _unwrap(await server.call_tool(name, valid))
    assert "valid" in res_valid
    res_invalid = _unwrap(await server.call_tool(name, invalid))
    assert "valid" in res_invalid


@pytest.mark.asyncio
async def test_parse_boleto_wrapper() -> None:
    server = build_server()
    res = _unwrap(await server.call_tool("parse_boleto", {"value": ""}))
    assert res["valid"] is False
    assert res["error"]["code"] == "EMPTY_INPUT"


@pytest.mark.asyncio
async def test_parse_pix_brcode_wrapper() -> None:
    server = build_server()
    res = _unwrap(await server.call_tool("parse_pix_brcode", {"value": "not-a-brcode"}))
    assert res["valid"] is False


@pytest.mark.asyncio
async def test_generate_pix_brcode_wrapper_valid() -> None:
    server = build_server()
    res = _unwrap(
        await server.call_tool(
            "generate_pix_brcode",
            {
                "chave": "user@example.com",
                "nome_beneficiario": "JOAO",
                "cidade": "SAO PAULO",
            },
        )
    )
    assert res["error"] is None
    assert res["brcode"]


@pytest.mark.asyncio
async def test_generate_pix_brcode_wrapper_missing_chave() -> None:
    server = build_server()
    res = _unwrap(
        await server.call_tool(
            "generate_pix_brcode",
            {
                "chave": "",
                "nome_beneficiario": "JOAO",
                "cidade": "SAO PAULO",
            },
        )
    )
    assert res["error"] is not None


@pytest.mark.asyncio
async def test_is_feriado_nacional_wrapper() -> None:
    server = build_server()
    res = _unwrap(await server.call_tool("is_feriado_nacional", {"date": "2026-09-07"}))
    assert res["is_feriado"] is True


@pytest.mark.asyncio
async def test_proximo_dia_util_wrapper() -> None:
    server = build_server()
    res = _unwrap(await server.call_tool("proximo_dia_util", {"date": "2026-09-06"}))
    assert "date" in res
    assert "dias_pulados" in res


@pytest.mark.asyncio
async def test_contar_dias_uteis_wrapper() -> None:
    server = build_server()
    res = _unwrap(
        await server.call_tool(
            "contar_dias_uteis",
            {"start_date": "2026-01-05", "end_date": "2026-01-12"},
        )
    )
    assert res["count"] >= 0
    assert res["total_dias"] == 7


@pytest.mark.asyncio
async def test_listar_feriados_wrapper() -> None:
    server = build_server()
    res = _unwrap(await server.call_tool("listar_feriados", {"year": 2026}))
    assert res["ano"] == 2026
    assert len(res["feriados"]) > 0
