"""Telemetria opt-in via PostHog. Default OFF. Anonymous metadata only.

Nunca registra inputs, outputs ou PII. Habilitar via env var
``BRASIL_MCP_TELEMETRY=1`` (também aceita ``true``, ``yes``, ``on``).
"""

from __future__ import annotations

import os
import platform
import sys
import time
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import brasil_mcp


def _is_enabled() -> bool:
    return os.environ.get("BRASIL_MCP_TELEMETRY", "0").lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def _data_dir() -> Path:
    base = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    p = Path(base) / "brasil-mcp"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _get_or_create_installation_id() -> str:
    f = _data_dir() / "installation_id"
    if f.exists():
        return f.read_text().strip()
    new_id = str(uuid.uuid4())
    f.write_text(new_id)
    return new_id


def _notice_seen() -> bool:
    return (_data_dir() / "notice_seen").exists()


def _mark_notice_seen() -> None:
    (_data_dir() / "notice_seen").touch()


def maybe_show_notice() -> None:
    """Mostra um aviso único no stderr se telemetria não estiver opt-in."""
    if _is_enabled() or _notice_seen():
        return
    print(
        "\n[info] Brasil MCP nao coleta telemetria. "
        "Para opt-in (anonymous metadata only):\n"
        "    export BRASIL_MCP_TELEMETRY=1\n",
        file=sys.stderr,
    )
    _mark_notice_seen()


_posthog_client: Any | None = None


def _get_client() -> Any | None:
    global _posthog_client
    if not _is_enabled():
        return None
    if _posthog_client is not None:
        return _posthog_client
    try:
        # Lazy import — só importa se opt-in. `posthog` é dep opcional.
        import posthog  # pyright: ignore[reportMissingImports]
    except ImportError:
        return None
    api_key = os.environ.get("BRASIL_MCP_POSTHOG_KEY", "phc_PUBLIC_KEY_PLACEHOLDER")
    _posthog_client = posthog.Posthog(api_key, host="https://us.i.posthog.com")
    return _posthog_client


def track_tool_call(
    tool: str,
    success: bool,
    latency_ms: float,
    error_code: str | None = None,
) -> None:
    """Registra uma chamada de ferramenta. No-op se telemetria desabilitada."""
    client = _get_client()
    if client is None:
        return
    try:
        client.capture(
            distinct_id=_get_or_create_installation_id(),
            event="tool_called",
            properties={
                "tool": tool,
                "success": success,
                "latency_ms": round(latency_ms, 3),
                "error_code": error_code,
                "brasil_mcp_version": brasil_mcp.__version__,
                "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
                "platform": platform.system().lower(),
            },
        )
    except Exception:
        # Falha de telemetria nunca deve quebrar a experiência do usuário.
        pass


@contextmanager
def track(tool: str) -> Iterator[None]:
    """Context manager para cronometrar + reportar uma chamada de tool.

    Exceções no código encapsulado continuam propagando; a telemetria apenas
    registra o erro antes de relançar.
    """
    start = time.perf_counter()
    error_code: str | None = None
    success = True
    try:
        yield
    except Exception as exc:
        success = False
        error_code = type(exc).__name__
        raise
    finally:
        latency_ms = (time.perf_counter() - start) * 1000
        track_tool_call(tool, success=success, latency_ms=latency_ms, error_code=error_code)
