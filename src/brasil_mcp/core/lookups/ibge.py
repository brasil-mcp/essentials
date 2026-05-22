"""lookup_ibge_municipio — IBGE Localidades API.

Aceita nome do município (case-insensitive, acentos toleráveis) + UF opcional.
"""

from __future__ import annotations

import unicodedata
from typing import Any

from brasil_mcp.core.cache import local as cache
from brasil_mcp.core.errors import ErrorCode, ErrorObj
from brasil_mcp.core.lookups.http_client import (
    NetworkError,
    UpstreamError,
    get_json,
)

# IBGE Localidades — lista municípios por UF. Buscamos por UF e filtramos local.
IBGE_MUNICIPIOS_BY_UF = (
    "https://servicodados.ibge.gov.br/api/v1/localidades/estados/{uf}/municipios"
)
CACHE_NAMESPACE = "ibge_uf_municipios"
CACHE_TTL = 30 * 24 * 60 * 60  # 30 days


def _normalize(s: str) -> str:
    nfkd = unicodedata.normalize("NFKD", s)
    no_accents = "".join(c for c in nfkd if not unicodedata.combining(c))
    return " ".join(no_accents.upper().split())


def lookup_ibge_municipio(nome: str, uf: str | None = None) -> dict[str, Any]:
    """Look up IBGE municipio code by name. UF narrows the search.

    Returns: { valid, nome, uf, ibge_code, raw_nome, raw_uf, error,
               matches: [{nome, uf, ibge_code}] }

    `matches` lists all candidates when ambiguous (homonymous cities across UFs)
    and the caller didn't pin a UF.
    """
    raw_nome = nome or ""
    raw_uf = uf or ""
    nome_norm = _normalize(raw_nome)
    uf_norm = raw_uf.strip().upper() or None

    if not nome_norm:
        return _err(
            raw_nome,
            raw_uf,
            ErrorCode.EMPTY_INPUT,
            "Nome de município obrigatório.",
            "Municipio name required.",
        )

    if uf_norm:
        matches = _search_within_uf(nome_norm, uf_norm)
        if matches is None:
            return _err(
                raw_nome,
                raw_uf,
                ErrorCode.NETWORK_ERROR,
                "Falha ao consultar IBGE.",
                "Failed to query IBGE.",
            )
    else:
        # Fan out across all 27 UFs (cached individually). Cost: 27 cache hits in
        # steady state, or 27 sequential HTTP calls on cold cache. Tolerable for
        # one-off lookups but slow on cold start.
        matches = []
        for uf_iter in _UFS_BRASIL:
            partial = _search_within_uf(nome_norm, uf_iter)
            if partial is None:
                return _err(
                    raw_nome,
                    raw_uf,
                    ErrorCode.NETWORK_ERROR,
                    "Falha ao consultar IBGE.",
                    "Failed to query IBGE.",
                )
            matches.extend(partial)

    if not matches:
        return _err(
            raw_nome,
            raw_uf,
            ErrorCode.NOT_FOUND,
            "Município não encontrado.",
            "Municipio not found.",
        )

    primary = matches[0]
    return {
        "valid": True,
        "nome": primary["nome"],
        "uf": primary["uf"],
        "ibge_code": primary["ibge_code"],
        "raw_nome": raw_nome,
        "raw_uf": raw_uf,
        "error": None,
        "matches": matches,
    }


def _search_within_uf(nome_norm: str, uf: str) -> list[dict[str, Any]] | None:
    """Returns list of matching municipios in `uf`, or None on network failure."""
    cached = cache.get(CACHE_NAMESPACE, uf)
    if cached is None:
        try:
            body = get_json(IBGE_MUNICIPIOS_BY_UF.format(uf=uf))
        except (NetworkError, UpstreamError):
            return None
        municipios = [
            {"nome": m["nome"], "uf": uf, "ibge_code": str(m["id"])}
            for m in body
            if isinstance(m, dict) and "id" in m and "nome" in m
        ]
        cache.set_(CACHE_NAMESPACE, uf, municipios, ttl_seconds=CACHE_TTL)
        cached = municipios
    return [m for m in cached if _normalize(m["nome"]) == nome_norm]


def _err(raw_nome: str, raw_uf: str, code: ErrorCode, pt: str, en: str) -> dict[str, Any]:
    return {
        "valid": False,
        "nome": None,
        "uf": None,
        "ibge_code": None,
        "raw_nome": raw_nome,
        "raw_uf": raw_uf,
        "error": ErrorObj(code, pt, en).to_dict(),
        "matches": [],
    }


_UFS_BRASIL = (
    "AC",
    "AL",
    "AM",
    "AP",
    "BA",
    "CE",
    "DF",
    "ES",
    "GO",
    "MA",
    "MG",
    "MS",
    "MT",
    "PA",
    "PB",
    "PE",
    "PI",
    "PR",
    "RJ",
    "RN",
    "RO",
    "RR",
    "RS",
    "SC",
    "SE",
    "SP",
    "TO",
)
