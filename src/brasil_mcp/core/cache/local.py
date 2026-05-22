"""File-based local cache with TTL — used by online lookup tools.

Cache directory: `$XDG_CACHE_HOME/brasil-mcp/lookups/` (defaults to
`~/.cache/brasil-mcp/lookups/` on Unix). Each entry is a JSON file with the
payload and an expiry timestamp.

Safe for single-process use. For multi-process / multi-host concurrency we'd
need a proper KV store — out of scope for v0.2.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def _cache_root() -> Path:
    base = os.environ.get("XDG_CACHE_HOME") or os.path.expanduser("~/.cache")
    return Path(base) / "brasil-mcp" / "lookups"


def _key_path(namespace: str, key: str) -> Path:
    """Map (namespace, key) to a filesystem path.

    The key is hashed to avoid path traversal / filename-length issues with
    arbitrary input (e.g., CEP "12345-678" or user-supplied municipio name).
    """
    safe_ns = "".join(c for c in namespace if c.isalnum() or c in "-_")
    key_hash = hashlib.sha256(key.encode("utf-8")).hexdigest()[:32]
    return _cache_root() / safe_ns / f"{key_hash}.json"


@dataclass(frozen=True, slots=True)
class CacheEntry:
    value: Any
    expires_at: float  # unix epoch seconds


def get(namespace: str, key: str, *, now: float | None = None) -> Any | None:
    """Return the cached value if present and not expired, else None."""
    path = _key_path(namespace, key)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None
    expires_at = data.get("expires_at", 0)
    current = now if now is not None else time.time()
    if expires_at < current:
        return None
    return data.get("value")


def set_(  # name avoids shadowing builtin set; used as cache.set_
    namespace: str,
    key: str,
    value: Any,
    *,
    ttl_seconds: float,
    now: float | None = None,
) -> None:
    """Store value under (namespace, key) with expiry now + ttl_seconds."""
    path = _key_path(namespace, key)
    path.parent.mkdir(parents=True, exist_ok=True)
    current = now if now is not None else time.time()
    payload = {"value": value, "expires_at": current + ttl_seconds}
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload))
    tmp.rename(path)


def clear(namespace: str | None = None) -> int:
    """Delete cache entries. If namespace is None, clears everything.

    Returns count of files removed.
    """
    root = _cache_root()
    if not root.exists():
        return 0
    target = root / namespace if namespace else root
    if not target.exists():
        return 0
    count = 0
    for p in target.rglob("*.json"):
        try:
            p.unlink()
            count += 1
        except OSError:  # pragma: no cover - filesystem race
            pass
    return count
