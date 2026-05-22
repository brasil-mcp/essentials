"""lookup_banco_febraban — banco brasileiro via BrasilAPI (200+ instituições).

Fallback opcional para o banco bundled em core/boleto/febraban_codes.json
quando o caller quiser cobertura ampla. Usado pelo MCP tool dedicado.
"""

from __future__ import annotations

from typing import Any

from brasil_mcp.core.cache import local as cache
from brasil_mcp.core.errors import ErrorCode, ErrorObj
from brasil_mcp.core.lookups.http_client import (
    NetworkError,
    NotFoundError,
    UpstreamError,
    get_json,
)

BRASILAPI_BANK_URL = "https://brasilapi.com.br/api/banks/v1/{codigo}"
CACHE_NAMESPACE = "banco_febraban"
CACHE_TTL = 7 * 24 * 60 * 60  # 7 days — banks list changes rarely


def lookup_banco_febraban(codigo: str) -> dict[str, Any]:
    """Look up a Brazilian bank by FEBRABAN code (3 digits, e.g., "341").

    Returns: { valid, codigo_febraban, ispb, nome, fullName, raw, error }.
    Source: BrasilAPI. Cached locally for 7 days.
    """
    raw = codigo or ""
    digits = "".join(ch for ch in raw if ch.isdigit())

    if not digits:
        return _err(
            raw,
            ErrorCode.EMPTY_INPUT,
            "Código FEBRABAN não pode ser vazio.",
            "FEBRABAN code cannot be empty.",
        )
    digits = digits.zfill(3)
    if len(digits) > 3:
        return _err(
            raw,
            ErrorCode.INVALID_LENGTH,
            f"Código FEBRABAN deve ter no máximo 3 dígitos; recebido {len(digits)}.",
            f"FEBRABAN code must have at most 3 digits; got {len(digits)}.",
        )

    cached = cache.get(CACHE_NAMESPACE, digits)
    if cached is not None:
        return cached

    try:
        body = get_json(BRASILAPI_BANK_URL.format(codigo=digits))
    except NotFoundError:
        return _err(raw, ErrorCode.NOT_FOUND, "Banco não encontrado.", "Bank not found.")
    except (NetworkError, UpstreamError) as exc:
        return _err(
            raw,
            ErrorCode.NETWORK_ERROR,
            f"Falha de rede ao consultar BrasilAPI: {exc}",
            f"Network failure querying BrasilAPI: {exc}",
        )

    result = {
        "valid": True,
        "codigo_febraban": str(body.get("code") or digits).zfill(3),
        "ispb": body.get("ispb"),
        "nome": body.get("name"),
        "fullName": body.get("fullName"),
        "raw": raw,
        "error": None,
    }
    cache.set_(CACHE_NAMESPACE, digits, result, ttl_seconds=CACHE_TTL)
    return result


def _err(raw: str, code: ErrorCode, pt: str, en: str) -> dict[str, Any]:
    return {
        "valid": False,
        "codigo_febraban": None,
        "ispb": None,
        "nome": None,
        "fullName": None,
        "raw": raw,
        "error": ErrorObj(code, pt, en).to_dict(),
    }
