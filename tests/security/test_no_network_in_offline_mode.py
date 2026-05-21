"""Verify core tools work fully offline.

When telemetry is OFF (the default), no validator / parser / calendar / pix
function should make any network call. We enforce this by patching
``socket.socket`` and ``urllib.request.urlopen`` to raise — any attempt to use
them blows up loudly.
"""

from __future__ import annotations

import socket
import urllib.request
from pathlib import Path

import pytest

from brasil_mcp.core import telemetry
from brasil_mcp.core.boleto.parser import parse_boleto
from brasil_mcp.core.calendar.feriados import (
    contar_dias_uteis,
    is_feriado_nacional,
    listar_feriados,
    proximo_dia_util,
)
from brasil_mcp.core.pix.parser import generate_pix_brcode, parse_pix_brcode
from brasil_mcp.core.validators.cnh import validate_cnh
from brasil_mcp.core.validators.cnpj import validate_cnpj
from brasil_mcp.core.validators.cpf import validate_cpf
from brasil_mcp.core.validators.credit_card import validate_credit_card
from brasil_mcp.core.validators.pis import validate_pis
from brasil_mcp.core.validators.renavam import validate_renavam
from brasil_mcp.core.validators.titulo_eleitor import validate_titulo_eleitor


@pytest.fixture
def offline(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Block all socket creation + HTTP calls + ensure telemetry is OFF."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    monkeypatch.delenv("BRASIL_MCP_TELEMETRY", raising=False)
    monkeypatch.setattr(telemetry, "_posthog_client", None)

    def blocked_socket(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise RuntimeError("network access not allowed in offline mode")

    def blocked_urlopen(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise RuntimeError("urlopen not allowed in offline mode")

    monkeypatch.setattr(socket, "socket", blocked_socket)
    monkeypatch.setattr(urllib.request, "urlopen", blocked_urlopen)


def test_validators_work_offline(offline: None) -> None:
    """Every validator works without any network access."""
    assert validate_cpf("52998224725").valid is True
    assert validate_cnpj("11222333000181").valid is True
    assert validate_pis("12056412348").valid in (True, False)
    assert validate_renavam("00482397500").valid in (True, False)
    assert validate_cnh("04607277401").valid in (True, False)
    assert validate_titulo_eleitor("123456789012").valid in (True, False)
    assert validate_credit_card("4111111111111111").valid is True


def test_pix_works_offline(offline: None) -> None:
    """generate_pix_brcode + parse_pix_brcode work fully offline."""
    out = generate_pix_brcode(
        chave="user@example.com",
        nome_beneficiario="JOAO",
        cidade="SP",
    )
    assert out["error"] is None
    parsed = parse_pix_brcode(out["brcode"])
    assert parsed.valid is True


def test_boleto_works_offline(offline: None) -> None:
    """parse_boleto works fully offline (reads only bundled JSON)."""
    # Use a known-bad input so we exercise the parser path without needing a
    # valid boleto in this test file. The fact that it returns a structured
    # result (rather than raising / hanging) is what we're verifying.
    result = parse_boleto("12345")
    assert result.valid is False


def test_calendar_works_offline(offline: None) -> None:
    """Calendar tools rely on bundled holidays data — fully offline."""
    assert is_feriado_nacional("2026-09-07")["is_feriado"] is True
    assert "date" in proximo_dia_util("2026-09-06")
    assert "count" in contar_dias_uteis("2026-01-05", "2026-01-12")
    assert listar_feriados(2026)["ano"] == 2026


def test_telemetry_default_no_socket(offline: None) -> None:
    """With telemetry OFF, track_tool_call must not touch the network."""
    # Should be a no-op — no socket attempts.
    telemetry.track_tool_call(tool="validate_cpf", success=True, latency_ms=1.0, error_code=None)
    # No exception = success.
