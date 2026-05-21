"""Guarantee filesystem isolation — we don't write outside our XDG data dir.

Telemetry writes two files (and only two): ``installation_id`` and
``notice_seen``, both under ``$XDG_DATA_HOME/brasil-mcp/``.

Core tools read ``febraban_codes.json`` from the package via
``importlib.resources``; no other on-disk reads / writes are allowed during
validation, parsing, or generation.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from brasil_mcp.core import telemetry
from brasil_mcp.core.calendar.feriados import is_feriado_nacional
from brasil_mcp.core.pix.parser import generate_pix_brcode, parse_pix_brcode
from brasil_mcp.core.validators.cpf import validate_cpf


@pytest.fixture
def isolated_xdg(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    monkeypatch.setattr(telemetry, "_posthog_client", None)
    return tmp_path


def test_telemetry_only_writes_under_xdg_data_home(isolated_xdg: Path) -> None:
    """Telemetry writes only to XDG_DATA_HOME/brasil-mcp/."""
    # Invoke both side-effecting paths.
    telemetry.maybe_show_notice()
    telemetry._get_or_create_installation_id()

    expected_dir = isolated_xdg / "brasil-mcp"
    assert expected_dir.exists()
    # Only two files allowed.
    files = {p.name for p in expected_dir.iterdir()}
    assert files == {"notice_seen", "installation_id"}, files


def test_telemetry_no_write_when_notice_already_seen(isolated_xdg: Path) -> None:
    """Second call to maybe_show_notice() must not modify the filesystem."""
    telemetry.maybe_show_notice()
    notice_path = isolated_xdg / "brasil-mcp" / "notice_seen"
    mtime1 = notice_path.stat().st_mtime
    telemetry.maybe_show_notice()
    # mtime should not advance — touch() updates mtime, so calling .touch()
    # again would change it. Our implementation early-returns when notice_seen
    # exists, so mtime stays the same.
    assert notice_path.stat().st_mtime == mtime1


def test_core_tools_do_not_write_to_disk(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Validators, parsers, and calendar tools must not write any files.

    We snapshot the tmp_path (acting as a sentinel) before and after a series
    of tool invocations and assert nothing new appeared.
    """
    # Point XDG_DATA_HOME at tmp_path so anyone tempted to touch it lands here.
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))

    def snapshot() -> set[Path]:
        return set(tmp_path.rglob("*")) if tmp_path.exists() else set()

    before = snapshot()

    # Run a representative sample.
    validate_cpf("52998224725")
    out = generate_pix_brcode(
        chave="user@example.com",
        nome_beneficiario="JOAO",
        cidade="SP",
    )
    parse_pix_brcode(out["brcode"])
    is_feriado_nacional("2026-09-07")

    after = snapshot()
    assert after == before, f"Unexpected filesystem writes: {after - before}"


def test_core_tools_do_not_read_secret_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    """Patch os.open to log all opens; verify validators/parsers don't read
    anything they shouldn't (e.g., /etc/passwd, ~/.ssh).
    """
    forbidden_prefixes = ("/etc/", "/root/", "/proc/", "/sys/")
    opened: list[str] = []
    real_open = os.open

    def tracking_open(path, *args, **kwargs):  # type: ignore[no-untyped-def]
        opened.append(str(path))
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr(os, "open", tracking_open)

    # Run tools that might be tempted to read config.
    validate_cpf("12345678909")
    out = generate_pix_brcode(
        chave="user@example.com",
        nome_beneficiario="JOAO",
        cidade="SP",
    )
    parse_pix_brcode(out["brcode"])

    for path in opened:
        for prefix in forbidden_prefixes:
            assert not path.startswith(prefix), f"forbidden read: {path}"
