"""lookup_cotacao_brl — cotação PTAX BCB.

Fonte oficial: Banco Central do Brasil, API Olinda PTAX. Sem autenticação.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from brasil_mcp.core.cache import local as cache
from brasil_mcp.core.errors import ErrorCode, ErrorObj
from brasil_mcp.core.lookups.http_client import (
    NetworkError,
    UpstreamError,
    get_json,
)

# Cotação de fechamento mais recente em ou antes da data informada.
BCB_PTAX_URL = (
    "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/"
    "CotacaoMoedaPeriodoFechamento(codigoMoeda=@codigoMoeda,"
    "dataInicial=@dataInicial,dataFinalCotacao=@dataFinalCotacao)"
)
CACHE_NAMESPACE = "cotacao_brl"

# Cotação histórica nunca muda — cache longo.
CACHE_TTL_HISTORICA = 365 * 24 * 60 * 60  # 1 year
# Cotação "hoje" pode estar vazia até BCB publicar — cache curto.
CACHE_TTL_RECENTE = 60 * 60  # 1 hour

SUPPORTED_MOEDAS = ("USD", "EUR", "GBP", "JPY", "ARS", "CHF", "CAD", "AUD")


def lookup_cotacao_brl(moeda: str, data_cotacao: str | None = None) -> dict[str, Any]:
    """Look up PTAX exchange rate from a foreign currency to BRL.

    Args:
        moeda: 3-letter ISO code (USD, EUR, GBP, JPY, ARS, CHF, CAD, AUD).
        data_cotacao: ISO date string (YYYY-MM-DD). Default: today.

    Returns: { valid, moeda, data_cotacao_efetiva, compra_cents, venda_cents,
               compra, venda, fonte, raw_moeda, raw_data, error }

    Notes:
        Prices returned both as int cents and original Decimal-formatted string.
        Weekends and BCB holidays don't have publication — the API returns the
        last business day prior. `data_cotacao_efetiva` reflects what was used.
    """
    raw_moeda = moeda or ""
    raw_data = data_cotacao or ""
    moeda_upper = raw_moeda.strip().upper()

    if not moeda_upper:
        return _err(
            raw_moeda, raw_data, ErrorCode.EMPTY_INPUT, "Moeda obrigatória.", "Currency required."
        )
    if moeda_upper not in SUPPORTED_MOEDAS:
        return _err(
            raw_moeda,
            raw_data,
            ErrorCode.UNSUPPORTED_FORMAT,
            f"Moeda '{moeda_upper}' não suportada. Suportadas: {', '.join(SUPPORTED_MOEDAS)}.",
            f"Currency '{moeda_upper}' not supported. Supported: {', '.join(SUPPORTED_MOEDAS)}.",
        )

    if raw_data:
        try:
            target_date = date.fromisoformat(raw_data)
        except ValueError:
            return _err(
                raw_moeda,
                raw_data,
                ErrorCode.INVALID_DATE,
                "Data inválida. Use formato YYYY-MM-DD.",
                "Invalid date. Use YYYY-MM-DD format.",
            )
    else:
        target_date = date.today()

    cache_key = f"{moeda_upper}-{target_date.isoformat()}"
    cached = cache.get(CACHE_NAMESPACE, cache_key)
    if cached is not None:
        return cached

    # Procura cotação em janela de 10 dias retroativa, pra cobrir feriados.
    start_date = target_date - timedelta(days=10)
    params = {
        "@codigoMoeda": f"'{moeda_upper}'",
        "@dataInicial": f"'{start_date.strftime('%m-%d-%Y')}'",
        "@dataFinalCotacao": f"'{target_date.strftime('%m-%d-%Y')}'",
        "$format": "json",
        "$top": "10",
        "$orderby": "dataHoraCotacao desc",
    }

    try:
        body = get_json(BCB_PTAX_URL, params=params)
    except (NetworkError, UpstreamError) as exc:
        return _err(
            raw_moeda,
            raw_data,
            ErrorCode.NETWORK_ERROR,
            f"Falha ao consultar BCB PTAX: {exc}",
            f"Failed to query BCB PTAX: {exc}",
        )

    rows = body.get("value") or []
    if not rows:
        return _err(
            raw_moeda,
            raw_data,
            ErrorCode.NOT_FOUND,
            f"Sem cotação disponível para {moeda_upper} em {target_date.isoformat()} ou dias anteriores.",
            f"No quote available for {moeda_upper} on or before {target_date.isoformat()}.",
        )

    row = rows[0]
    compra = Decimal(str(row.get("cotacaoCompra")))
    venda = Decimal(str(row.get("cotacaoVenda")))
    data_efetiva = row.get("dataHoraCotacao", "")[:10]

    result = {
        "valid": True,
        "moeda": moeda_upper,
        "data_cotacao_efetiva": data_efetiva,
        "compra_cents": round(compra * 100),
        "venda_cents": round(venda * 100),
        "compra": str(compra),
        "venda": str(venda),
        "fonte": "BCB PTAX",
        "raw_moeda": raw_moeda,
        "raw_data": raw_data,
        "error": None,
    }

    ttl = CACHE_TTL_RECENTE if (date.today() - target_date).days < 2 else CACHE_TTL_HISTORICA
    cache.set_(CACHE_NAMESPACE, cache_key, result, ttl_seconds=ttl)
    return result


def _err(raw_moeda: str, raw_data: str, code: ErrorCode, pt: str, en: str) -> dict[str, Any]:
    return {
        "valid": False,
        "moeda": None,
        "data_cotacao_efetiva": None,
        "compra_cents": None,
        "venda_cents": None,
        "compra": None,
        "venda": None,
        "fonte": None,
        "raw_moeda": raw_moeda,
        "raw_data": raw_data,
        "error": ErrorObj(code, pt, en).to_dict(),
    }
