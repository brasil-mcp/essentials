"""Test the PostHog opt-in path in core/telemetry.py.

PostHog is an optional dep; for tests we inject a fake `posthog` module into
``sys.modules`` so the lazy import in `_get_client` picks it up.
"""

from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

from brasil_mcp.core import telemetry


@pytest.fixture(autouse=True)
def _isolate_filesystem(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Each test gets its own XDG_DATA_HOME and a fresh client cache."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    monkeypatch.setattr(telemetry, "_posthog_client", None)


class _FakePosthog:
    """Captures calls to .capture()."""

    def __init__(self, api_key: str, host: str) -> None:
        self.api_key = api_key
        self.host = host
        self.captures: list[dict] = []

    def capture(self, **kwargs: object) -> None:
        self.captures.append(kwargs)


def _install_fake_posthog(
    monkeypatch: pytest.MonkeyPatch, raise_on_capture: bool = False
) -> _FakePosthog | None:
    """Install a fake `posthog` module in sys.modules.

    The Posthog class is exposed at posthog.Posthog. We return the instance
    that will be created when `_get_client` calls `posthog.Posthog(...)`.
    """
    instances: list[_FakePosthog] = []

    class _PosthogClass:
        def __new__(cls, api_key: str, host: str) -> _FakePosthog:  # type: ignore[misc]
            inst = _FakePosthog(api_key, host)
            if raise_on_capture:
                original_capture = inst.capture

                def boom(**kwargs: object) -> None:
                    original_capture(**kwargs)
                    raise RuntimeError("posthog network failure")

                inst.capture = boom  # type: ignore[method-assign]
            instances.append(inst)
            return inst

    fake_module = types.ModuleType("posthog")
    fake_module.Posthog = _PosthogClass  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "posthog", fake_module)

    # Return a thunk-like holder. After _get_client runs, instances[0] is set.
    class _Holder:
        @property
        def value(self) -> _FakePosthog | None:
            return instances[0] if instances else None

    holder = _Holder()
    return holder  # type: ignore[return-value]


def test_get_client_returns_none_when_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    """Line 73-74: opt-out → _get_client returns None."""
    monkeypatch.delenv("BRASIL_MCP_TELEMETRY", raising=False)
    assert telemetry._get_client() is None


def test_get_client_cached_on_second_call(monkeypatch: pytest.MonkeyPatch) -> None:
    """Line 76: cached client returned without re-importing posthog."""
    monkeypatch.setenv("BRASIL_MCP_TELEMETRY", "1")
    holder = _install_fake_posthog(monkeypatch)

    c1 = telemetry._get_client()
    c2 = telemetry._get_client()
    assert c1 is c2  # cache hit
    assert holder.value is c1  # type: ignore[attr-defined]


def test_track_tool_call_sends_to_posthog_when_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Lines 97-110: when opt-in, track_tool_call calls client.capture with the
    documented properties shape.
    """
    monkeypatch.setenv("BRASIL_MCP_TELEMETRY", "1")
    holder = _install_fake_posthog(monkeypatch)

    telemetry.track_tool_call(
        tool="validate_cpf",
        success=True,
        latency_ms=2.5,
        error_code=None,
    )
    inst = holder.value  # type: ignore[attr-defined]
    assert inst is not None
    assert len(inst.captures) == 1
    cap = inst.captures[0]
    assert cap["event"] == "tool_called"
    props = cap["properties"]
    assert props["tool"] == "validate_cpf"
    assert props["success"] is True
    assert props["latency_ms"] == 2.5
    assert props["error_code"] is None
    assert "brasil_mcp_version" in props
    assert "python_version" in props
    assert "platform" in props
    # distinct_id should be a uuid string (from _get_or_create_installation_id).
    assert isinstance(cap["distinct_id"], str)
    assert len(cap["distinct_id"]) > 0


def test_track_tool_call_swallows_posthog_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Lines 111-113: any exception from posthog must be silently swallowed —
    telemetry failures must NEVER break the user's tool call.
    """
    monkeypatch.setenv("BRASIL_MCP_TELEMETRY", "1")
    _install_fake_posthog(monkeypatch, raise_on_capture=True)

    # Should NOT raise.
    telemetry.track_tool_call(
        tool="validate_cpf",
        success=False,
        latency_ms=1.0,
        error_code="ValueError",
    )


def test_track_tool_call_with_error_code(monkeypatch: pytest.MonkeyPatch) -> None:
    """Cover the `error_code` non-None branch."""
    monkeypatch.setenv("BRASIL_MCP_TELEMETRY", "1")
    holder = _install_fake_posthog(monkeypatch)

    telemetry.track_tool_call(
        tool="validate_cnpj",
        success=False,
        latency_ms=0.1,
        error_code="INVALID_LENGTH",
    )
    inst = holder.value  # type: ignore[attr-defined]
    assert inst.captures[0]["properties"]["error_code"] == "INVALID_LENGTH"
