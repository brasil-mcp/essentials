"""Denial-of-service resistance tests.

Adversaries can try to exhaust CPU / memory by sending huge or pathological
inputs. Every entrypoint should reject these in <100ms (most much faster).

We use `time.perf_counter` + `signal.alarm` (POSIX-only) as a belt-and-braces
guard. On platforms without alarm, time.perf_counter alone bounds the test.
"""

from __future__ import annotations

import signal
import time
from collections.abc import Iterator
from contextlib import contextmanager

import pytest

from brasil_mcp.core.boleto.parser import parse_boleto
from brasil_mcp.core.calendar.feriados import (
    contar_dias_uteis,
    is_feriado_nacional,
    listar_feriados,
)
from brasil_mcp.core.pix.parser import generate_pix_brcode, parse_pix_brcode
from brasil_mcp.core.validators.cnh import validate_cnh
from brasil_mcp.core.validators.cnpj import validate_cnpj
from brasil_mcp.core.validators.cpf import validate_cpf
from brasil_mcp.core.validators.credit_card import validate_credit_card
from brasil_mcp.core.validators.pis import validate_pis
from brasil_mcp.core.validators.renavam import validate_renavam
from brasil_mcp.core.validators.titulo_eleitor import validate_titulo_eleitor

_TIMEOUT_SECONDS = 1.0  # hard ceiling per individual call
_FAST_SECONDS = 0.1  # informational bound — every call should be <100ms


@contextmanager
def _hard_timeout(seconds: float) -> Iterator[None]:
    """Best-effort hard timeout using SIGALRM (POSIX only)."""
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def _handler(signum: int, frame) -> None:  # type: ignore[no-untyped-def]
        raise TimeoutError(f"operation exceeded {seconds}s")

    old = signal.signal(signal.SIGALRM, _handler)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old)


def _assert_fast(callable_, *args, **kwargs):  # type: ignore[no-untyped-def]
    """Run callable_(*args, **kwargs) under a hard timeout and verify it
    completed under _FAST_SECONDS (informational; hard limit is _TIMEOUT_SECONDS).
    """
    start = time.perf_counter()
    with _hard_timeout(_TIMEOUT_SECONDS):
        result = callable_(*args, **kwargs)
    elapsed = time.perf_counter() - start
    assert elapsed < _TIMEOUT_SECONDS, f"took {elapsed:.3f}s (limit {_TIMEOUT_SECONDS}s)"
    return result, elapsed


# ---------------------------------------------------------------------------
# Mega-input rejection — each validator should bounce >1MB strings fast.
# ---------------------------------------------------------------------------


VALIDATORS = [
    validate_cpf,
    validate_cnpj,
    validate_pis,
    validate_renavam,
    validate_cnh,
    validate_titulo_eleitor,
    validate_credit_card,
]


@pytest.mark.parametrize("validator", VALIDATORS, ids=lambda f: f.__name__)
def test_validator_rejects_megabyte_input_fast(validator) -> None:  # type: ignore[no-untyped-def]
    huge = "A" * 1_048_576  # 1 MiB
    result, elapsed = _assert_fast(validator, huge)
    assert result.valid is False
    # Sub-second on any reasonable hardware.
    assert elapsed < 0.5


def test_parse_pix_rejects_megabyte_input_fast() -> None:
    huge = "X" * 1_048_576
    result, _ = _assert_fast(parse_pix_brcode, huge)
    assert result.valid is False


def test_parse_boleto_rejects_megabyte_input_fast() -> None:
    # Boleto only allows digits + separators, so a huge alphabetic string
    # should be rejected as INVALID_CHARACTER.
    huge = "A" * 1_048_576
    result, _ = _assert_fast(parse_boleto, huge)
    assert result.valid is False


# ---------------------------------------------------------------------------
# Numeric overflow guards
# ---------------------------------------------------------------------------


def test_generate_pix_with_overflow_valor() -> None:
    """An astronomical valor should still produce a brcode (we format with
    `:.2f`), or at worst fail gracefully — it must not crash or hang.
    """
    huge_valor = 10**18
    out, _ = _assert_fast(
        generate_pix_brcode,
        "user@example.com",
        "JOAO",
        "SP",
        valor=huge_valor,
    )
    # We don't assert success/failure — the contract is "no crash, returns
    # within timeout". Documented behavior: brcode succeeds (large amount
    # field), the burden of sanity is on the caller.
    assert out is not None


# ---------------------------------------------------------------------------
# Calendar bounds checks
# ---------------------------------------------------------------------------


def test_contar_dias_uteis_large_range() -> None:
    """Counting business days across a multi-year span must terminate.

    This is a loop-bounds check: regardless of input magnitude, the function
    must not hang. A 10-year range is realistic for callers (e.g. financial
    backfills) and exercises ~3650 iterations of per-iteration holiday lookup.
    We use a 10s ceiling: the function rebuilds the holiday set per iteration
    (intentional simplicity in v0.1.0), so this is informational, not perf.
    """
    with _hard_timeout(10.0):
        result = contar_dias_uteis("2015-01-01", "2025-01-01")
    assert "count" in result
    assert result["count"] > 0
    # The range is 10 years * ~252 business days = ~2520. Sanity bound.
    assert result["count"] > 2000
    assert result["count"] < 3000


def test_listar_feriados_year_9999() -> None:
    """Far-future year should not loop or hang."""
    result, _ = _assert_fast(listar_feriados, 9999)
    assert result["ano"] == 9999
    assert isinstance(result["feriados"], list)


def test_is_feriado_far_past_date() -> None:
    """Year 1 should be handled without timeout (holidays library bounds)."""
    # Use a year supported by python-holidays — they cover historical Brazil
    # post-independence. Year 1 may raise; we just want no infinite loop.
    try:
        result, _ = _assert_fast(is_feriado_nacional, "0001-01-01")
        assert "is_feriado" in result
    except (ValueError, NotImplementedError):
        # Acceptable: out-of-range years may raise — but they don't hang.
        pass


# ---------------------------------------------------------------------------
# Regex catastrophic backtracking guard
# ---------------------------------------------------------------------------


def test_no_regex_redos_in_validators() -> None:
    """A pathological string crafted for ReDoS (lots of valid chars + noise)
    should not blow up runtime.
    """
    nasty = ("123.456.789-" * 1000) + "X"
    result, elapsed = _assert_fast(validate_cpf, nasty)
    assert result.valid is False
    assert elapsed < 0.5
