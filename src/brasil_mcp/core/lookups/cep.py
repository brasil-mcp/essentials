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


# -------- Reverse lookup: endereço → lista de CEPs (via ViaCEP) --------

# ViaCEP exige UF + cidade + logradouro, todos com ≥3 caracteres.
VIACEP_REVERSE_URL = "https://viacep.com.br/ws/{uf}/{cidade}/{logradouro}/json/"
REVERSE_CACHE_NAMESPACE = "endereco_cep"
REVERSE_CACHE_TTL = 30 * 24 * 60 * 60  # 30 dias (mesma estabilidade do forward)

_MIN_TERM_LEN = 3


def lookup_endereco_cep(uf: str, cidade: str, logradouro: str) -> dict[str, Any]:
    """Busca lista de CEPs que casam com (UF, cidade, logradouro) via ViaCEP.

    Todos os 3 campos são obrigatórios. ViaCEP exige ≥3 caracteres em cada e
    aplica fuzzy matching no logradouro (busca por substring case-insensitive
    + accent-insensitive lado servidor).

    Returns: { valid, count, matches: [{cep, logradouro, complemento, unidade,
                                         bairro, cidade, uf, ibge, ddd}], raw, error }.
    Cacheado localmente por 30 dias por tupla (uf, cidade, logradouro).
    """
    raw = {"uf": uf or "", "cidade": cidade or "", "logradouro": logradouro or ""}
    uf_norm = (uf or "").strip().upper()
    cidade_norm = (cidade or "").strip()
    logradouro_norm = (logradouro or "").strip()

    if not uf_norm or not cidade_norm or not logradouro_norm:
        return _reverse_err(
            raw,
            ErrorCode.EMPTY_INPUT,
            "uf, cidade e logradouro são obrigatórios.",
            "uf, cidade and logradouro are required.",
        )
    if len(uf_norm) != 2:
        return _reverse_err(
            raw,
            ErrorCode.INVALID_LENGTH,
            f"UF deve ter 2 caracteres; recebido {len(uf_norm)}.",
            f"UF must have 2 chars; got {len(uf_norm)}.",
        )
    if len(cidade_norm) < _MIN_TERM_LEN or len(logradouro_norm) < _MIN_TERM_LEN:
        return _reverse_err(
            raw,
            ErrorCode.INVALID_LENGTH,
            f"cidade e logradouro precisam de pelo menos {_MIN_TERM_LEN} caracteres cada (limite ViaCEP).",
            f"cidade and logradouro need at least {_MIN_TERM_LEN} chars each (ViaCEP limit).",
        )

    cache_key = f"{uf_norm}|{cidade_norm.lower()}|{logradouro_norm.lower()}"
    cached = cache.get(REVERSE_CACHE_NAMESPACE, cache_key)
    if cached is not None:
        return cached

    # ViaCEP precisa de URL-encoded path segments. httpx faz isso ao passar como params,
    # mas aqui são path components — formatamos manualmente usando urllib.
    from urllib.parse import quote

    url = VIACEP_REVERSE_URL.format(
        uf=quote(uf_norm, safe=""),
        cidade=quote(cidade_norm, safe=""),
        logradouro=quote(logradouro_norm, safe=""),
    )

    try:
        body = get_json(url)
    except NotFoundError:
        return _reverse_err(
            raw, ErrorCode.NOT_FOUND, "Endereço não encontrado.", "Address not found."
        )
    except (NetworkError, UpstreamError) as exc:
        return _reverse_err(
            raw,
            ErrorCode.NETWORK_ERROR,
            f"Falha de rede ao consultar ViaCEP: {exc}",
            f"Network failure querying ViaCEP: {exc}",
        )

    # ViaCEP signals "no results" with an empty list (200) OR object {"erro": true}.
    if isinstance(body, dict) and body.get("erro"):
        return _reverse_err(
            raw, ErrorCode.NOT_FOUND, "Endereço não encontrado.", "Address not found."
        )
    if not isinstance(body, list) or not body:
        return _reverse_err(
            raw, ErrorCode.NOT_FOUND, "Endereço não encontrado.", "Address not found."
        )

    matches = [
        {
            "cep": (m.get("cep") or "").replace("-", ""),
            "logradouro": m.get("logradouro") or None,
            "complemento": m.get("complemento") or None,
            "unidade": m.get("unidade") or None,
            "bairro": m.get("bairro") or None,
            "cidade": m.get("localidade") or None,
            "uf": m.get("uf") or None,
            "ibge": m.get("ibge") or None,
            "ddd": m.get("ddd") or None,
        }
        for m in body
        if isinstance(m, dict)
    ]
    result = {
        "valid": True,
        "count": len(matches),
        "matches": matches,
        "raw": raw,
        "error": None,
    }
    cache.set_(REVERSE_CACHE_NAMESPACE, cache_key, result, ttl_seconds=REVERSE_CACHE_TTL)
    return result


def _reverse_err(raw: dict, code: ErrorCode, pt: str, en: str) -> dict[str, Any]:
    return {
        "valid": False,
        "count": 0,
        "matches": [],
        "raw": raw,
        "error": ErrorObj(code, pt, en).to_dict(),
    }
