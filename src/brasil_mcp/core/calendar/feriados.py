"""Ferramentas de calendário brasileiro: feriados e dias úteis.

Quatro funções puras, todas retornam ``dict[str, Any]`` com shape próprio
(distinto de :class:`brasil_mcp.core.models.ValidationResult`).
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

import holidays


def _parse_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def _br_holidays(year: int, uf: str | None = None):
    if uf:
        return holidays.country_holidays("BR", subdiv=uf, years=year)
    return holidays.country_holidays("BR", years=year)


def _is_holiday(d: date, uf: str | None) -> tuple[bool, str | None, str | None]:
    """Return (is_feriado, nome, esfera)."""
    national = _br_holidays(d.year, uf=None)
    if d in national:
        return True, national[d], "nacional"
    if uf:
        state = _br_holidays(d.year, uf=uf)
        if d in state:
            return True, state[d], "estadual"
    return False, None, None


def is_feriado_nacional(
    date_str: str,
    uf: str | None = None,
    municipio: str | None = None,
) -> dict[str, Any]:
    """Verifica se uma data é feriado brasileiro.

    Args:
        date_str: Data ISO ``YYYY-MM-DD``.
        uf: Sigla do estado (opcional) para incluir feriados estaduais.
        municipio: Aceito para futura extensão; ignorado em v0.1.0.

    Returns:
        ``{"is_feriado": bool, "nome": str|None, "esfera": "nacional"|"estadual"|None,
        "raw_date": str}``.
    """
    # municipio is accepted for future extensibility but unused in v0.1.0 because
    # the holidays library has limited municipal coverage for Brazil.
    _ = municipio
    d = _parse_date(date_str)
    is_feriado, nome, esfera = _is_holiday(d, uf=uf)
    return {
        "is_feriado": is_feriado,
        "nome": nome,
        "esfera": esfera,
        "raw_date": date_str,
    }


def proximo_dia_util(
    date_str: str,
    uf: str | None = None,
    include_today: bool = False,
) -> dict[str, Any]:
    """Retorna o próximo dia útil a partir de uma data.

    Args:
        date_str: Data ISO ``YYYY-MM-DD``.
        uf: Sigla do estado (opcional) — feriados estaduais contam como não-úteis.
        include_today: Se ``True`` e a própria data já for dia útil, retorna-a.

    Returns:
        ``{"date": str, "dias_pulados": int}``.
    """
    current = _parse_date(date_str)
    dias_pulados = 0
    if not include_today:
        current += timedelta(days=1)
        dias_pulados += 1

    while True:
        is_weekend = current.weekday() >= 5
        is_feriado, _nome, _esfera = _is_holiday(current, uf=uf)
        if not is_weekend and not is_feriado:
            break
        current += timedelta(days=1)
        dias_pulados += 1

    return {
        "date": current.isoformat(),
        "dias_pulados": dias_pulados,
    }


def contar_dias_uteis(
    start_date: str,
    end_date: str,
    uf: str | None = None,
    inclusive_end: bool = False,
) -> dict[str, Any]:
    """Conta dias úteis entre duas datas.

    Args:
        start_date: Data inicial (inclusiva) ISO ``YYYY-MM-DD``.
        end_date: Data final ISO ``YYYY-MM-DD``.
        uf: Sigla do estado (opcional).
        inclusive_end: Se ``True``, inclui ``end_date`` na contagem.

    Returns:
        ``{"count": int, "total_dias": int, "feriados_no_periodo":
        list[{date, nome}]}``.
    """
    start = _parse_date(start_date)
    end = _parse_date(end_date)
    stop = end + timedelta(days=1) if inclusive_end else end

    count = 0
    total = 0
    feriados_no_periodo: list[dict[str, str]] = []

    current = start
    while current < stop:
        total += 1
        is_weekend = current.weekday() >= 5
        is_feriado, nome, _esfera = _is_holiday(current, uf=uf)
        if is_feriado and nome is not None:
            feriados_no_periodo.append({"date": current.isoformat(), "nome": nome})
        if not is_weekend and not is_feriado:
            count += 1
        current += timedelta(days=1)

    return {
        "count": count,
        "total_dias": total,
        "feriados_no_periodo": feriados_no_periodo,
    }


def listar_feriados(year: int, uf: str | None = None) -> dict[str, Any]:
    """Lista feriados brasileiros para um ano.

    Args:
        year: Ano (ex: ``2026``).
        uf: Sigla do estado (opcional) — adiciona feriados estaduais.

    Returns:
        ``{"ano": int, "uf": str|None, "feriados": list[{date, nome, esfera}]}``
        ordenado por data.
    """
    national = _br_holidays(year, uf=None)
    feriados: list[dict[str, Any]] = [
        {"date": d.isoformat(), "nome": nome, "esfera": "nacional"} for d, nome in national.items()
    ]
    national_dates = {d for d in national}

    if uf:
        state = _br_holidays(year, uf=uf)
        for d, nome in state.items():
            if d in national_dates:
                continue
            feriados.append({"date": d.isoformat(), "nome": nome, "esfera": "estadual"})

    feriados.sort(key=lambda x: x["date"])

    return {
        "ano": year,
        "uf": uf,
        "feriados": feriados,
    }
