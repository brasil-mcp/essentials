"""Test the `python -m brasil_mcp` entry path."""

from __future__ import annotations

import runpy
import subprocess
import sys

import pytest

import brasil_mcp


def test_dunder_main_module_importable() -> None:
    """Importing the module should not invoke the CLI (guarded by __main__ check)."""
    import brasil_mcp.__main__ as main_mod

    # `app` should be the Typer instance exposed by the cli module.
    from brasil_mcp.adapters.cli.app import app

    assert main_mod.app is app


def test_python_m_brasil_mcp_version() -> None:
    """`python -m brasil_mcp version` should print the version on stdout.

    Smoke test for the subprocess path (verifies the entry script works
    end-to-end on a freshly forked interpreter).
    """
    result = subprocess.run(
        [sys.executable, "-m", "brasil_mcp", "version"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == brasil_mcp.__version__


@pytest.mark.filterwarnings("ignore::RuntimeWarning")
def test_run_module_executes_app_block(monkeypatch: pytest.MonkeyPatch) -> None:
    """Exercise `__main__.py` under coverage by running it via runpy as `__main__`.

    We stub the Typer `app` callable so it doesn't actually parse argv / exit.
    """
    import brasil_mcp.adapters.cli.app as cli_app_mod

    called = {"ran": False}

    def fake_app(*args, **kwargs) -> None:  # type: ignore[no-untyped-def]
        called["ran"] = True

    monkeypatch.setattr(cli_app_mod, "app", fake_app)

    # Running with run_name="__main__" executes the `if __name__ == "__main__"`
    # block, which calls `app()` — i.e. our `fake_app`.
    runpy.run_module("brasil_mcp", run_name="__main__")
    assert called["ran"] is True
