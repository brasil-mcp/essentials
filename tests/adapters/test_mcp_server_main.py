"""Exercise the `main()` entry point of the MCP server adapter."""

from __future__ import annotations

from pathlib import Path

import pytest

from brasil_mcp.adapters.mcp import server as server_mod


def test_main_invokes_run_and_notice(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """main() should call maybe_show_notice() then build_server().run()."""
    # Isolate XDG_DATA_HOME so we don't touch real user state.
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    # Make sure telemetry is disabled (default), so notice is shown.
    monkeypatch.delenv("BRASIL_MCP_TELEMETRY", raising=False)

    run_calls = {"ran": False}

    class _FakeServer:
        def run(self) -> None:
            run_calls["ran"] = True

    monkeypatch.setattr(server_mod, "build_server", lambda: _FakeServer())

    server_mod.main()
    assert run_calls["ran"] is True
