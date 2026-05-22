"""lookup_cep — endereço por CEP via ViaCEP."""

from __future__ import annotations

import re
from typing import Any

from brasil_mcp.core.cache import local as cache
from brasil_mcp.core.errors import ErrorCode, ErrorObj
from brasil_mcp.core.lookups.http_client import (
    NetworkError,
    NotFoundError,
    UpstreamError,
    get_json,
)

VIACEP_URL = "https://viacep.com.br/ws/{cep}/json/"
CACHE_NAMESPACE = "cep"
CACHE_TTL = 30 * 24 * 60 * 60  # 30 days — CEP data is very stable


def _normalize_cep(value: str) -> str:
    return re.sub(r"\D", "", value or "")


def lookup_cep(cep: str) -> dict[str, Any]:
    """Look up Brazilian postal code (CEP) via ViaCEP.

    Returns: { valid, cep, logradouro, complemento, bairro, cidade, uf,
               ibge, ddd, raw, error }

    `valid: false` if CEP malformed, not found, or network failure. Cached
    locally for 30 days per CEP.
    """
    raw = cep or ""
    digits = _normalize_cep(raw)

    if not digits:
        return _err(raw, ErrorCode.EMPTY_INPUT, "CEP não pode ser vazio.", "CEP cannot be empty.")
    if len(digits) != 8:
        return _err(
            raw,
            ErrorCode.INVALID_LENGTH,
            f"CEP deve ter 8 dígitos; recebido {len(digits)}.",
            f"CEP must have 8 digits; got {len(digits)}.",
        )

    cached = cache.get(CACHE_NAMESPACE, digits)
    if cached is not None:
        return cached

    try:
        body = get_json(VIACEP_URL.format(cep=digits))
    except NotFoundError:
        return _err(raw, ErrorCode.NOT_FOUND, "CEP não encontrado.", "CEP not found.")
    except (NetworkError, UpstreamError) as exc:
        return _err(
            raw,
            ErrorCode.NETWORK_ERROR,
            f"Falha de rede ao consultar ViaCEP: {exc}",
            f"Network failure querying ViaCEP: {exc}",
        )

    # ViaCEP signals "not found" via {"erro": "true"} (or boolean true)
    if isinstance(body, dict) and body.get("erro"):
        return _err(raw, ErrorCode.NOT_FOUND, "CEP não encontrado.", "CEP not found.")

    result = {
        "valid": True,
        "cep": digits,
        "logradouro": body.get("logradouro") or None,
        "complemento": body.get("complemento") or None,
        "bairro": body.get("bairro") or None,
        "cidade": body.get("localidade") or None,
        "uf": body.get("uf") or None,
        "ibge": body.get("ibge") or None,
        "ddd": body.get("ddd") or None,
        "raw": raw,
        "error": None,
    }
    cache.set_(CACHE_NAMESPACE, digits, result, ttl_seconds=CACHE_TTL)
    return result


def _err(raw: str, code: ErrorCode, pt: str, en: str) -> dict[str, Any]:
    return {
        "valid": False,
        "cep": None,
        "logradouro": None,
        "complemento": None,
        "bairro": None,
        "cidade": None,
        "uf": None,
        "ibge": None,
        "ddd": None,
        "raw": raw,
        "error": ErrorObj(code, pt, en).to_dict(),
    }
