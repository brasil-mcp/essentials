"""lookup_ddd — UF e cidades por código DDD via BrasilAPI."""

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

BRASILAPI_DDD_URL = "https://brasilapi.com.br/api/ddd/v1/{ddd}"
CACHE_NAMESPACE = "ddd"
CACHE_TTL = 90 * 24 * 60 * 60  # 90 days — DDD assignments are very stable


def lookup_ddd(ddd: str | int) -> dict[str, Any]:
    """Look up UF + list of municipios served by a 2-digit DDD area code.

    Returns: { valid, ddd, uf, cidades: [str], raw, error }.
    """
    raw = str(ddd) if ddd is not None else ""
    digits = "".join(ch for ch in raw if ch.isdigit())

    if not digits:
        return _err(raw, ErrorCode.EMPTY_INPUT, "DDD não pode ser vazio.", "DDD cannot be empty.")
    if len(digits) != 2:
        return _err(
            raw,
            ErrorCode.INVALID_LENGTH,
            f"DDD deve ter 2 dígitos; recebido {len(digits)}.",
            f"DDD must have 2 digits; got {len(digits)}.",
        )

    cached = cache.get(CACHE_NAMESPACE, digits)
    if cached is not None:
        return cached

    try:
        body = get_json(BRASILAPI_DDD_URL.format(ddd=digits))
    except NotFoundError:
        return _err(raw, ErrorCode.NOT_FOUND, "DDD não encontrado.", "DDD not found.")
    except (NetworkError, UpstreamError) as exc:
        return _err(
            raw,
            ErrorCode.NETWORK_ERROR,
            f"Falha de rede ao consultar BrasilAPI: {exc}",
            f"Network failure querying BrasilAPI: {exc}",
        )

    cidades = body.get("cities") or body.get("cidades") or []
    result = {
        "valid": True,
        "ddd": digits,
        "uf": (body.get("state") or body.get("uf") or "").upper() or None,
        "cidades": [str(c) for c in cidades],
        "raw": raw,
        "error": None,
    }
    cache.set_(CACHE_NAMESPACE, digits, result, ttl_seconds=CACHE_TTL)
    return result


def _err(raw: str, code: ErrorCode, pt: str, en: str) -> dict[str, Any]:
    return {
        "valid": False,
        "ddd": None,
        "uf": None,
        "cidades": [],
        "raw": raw,
        "error": ErrorObj(code, pt, en).to_dict(),
    }
