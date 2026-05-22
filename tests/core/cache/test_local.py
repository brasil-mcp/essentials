"""Tests for the file-based local cache."""

from __future__ import annotations

import time

import pytest

from brasil_mcp.core.cache import local as cache


@pytest.fixture(autouse=True)
def isolated_cache(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    yield


def test_set_get_roundtrip() -> None:
    cache.set_("test_ns", "key1", {"hello": "world"}, ttl_seconds=60)
    assert cache.get("test_ns", "key1") == {"hello": "world"}


def test_missing_key_returns_none() -> None:
    assert cache.get("test_ns", "nonexistent") is None


def test_expired_returns_none() -> None:
    cache.set_("ns", "key", "val", ttl_seconds=60, now=1000.0)
    # Asking at time 1061: expired
    assert cache.get("ns", "key", now=1061.0) is None


def test_just_before_expiry_hits() -> None:
    cache.set_("ns", "key", "val", ttl_seconds=60, now=1000.0)
    # Asking at time 1059: still valid
    assert cache.get("ns", "key", now=1059.0) == "val"


def test_corrupt_file_returns_none(tmp_path) -> None:
    cache.set_("ns", "key", "val", ttl_seconds=60)
    # Find the file and corrupt it
    files = list((tmp_path / "brasil-mcp" / "lookups" / "ns").iterdir())
    assert files
    files[0].write_text("not valid json {{{")
    assert cache.get("ns", "key") is None


def test_namespace_isolation() -> None:
    cache.set_("ns_a", "key", "value_a", ttl_seconds=60)
    cache.set_("ns_b", "key", "value_b", ttl_seconds=60)
    assert cache.get("ns_a", "key") == "value_a"
    assert cache.get("ns_b", "key") == "value_b"


def test_clear_namespace() -> None:
    cache.set_("ns_a", "k1", "v1", ttl_seconds=60)
    cache.set_("ns_a", "k2", "v2", ttl_seconds=60)
    cache.set_("ns_b", "k3", "v3", ttl_seconds=60)
    removed = cache.clear("ns_a")
    assert removed == 2
    assert cache.get("ns_a", "k1") is None
    assert cache.get("ns_b", "k3") == "v3"


def test_clear_all() -> None:
    cache.set_("ns_a", "k1", "v1", ttl_seconds=60)
    cache.set_("ns_b", "k2", "v2", ttl_seconds=60)
    removed = cache.clear()
    assert removed == 2


def test_clear_nonexistent_namespace_returns_zero() -> None:
    assert cache.clear("never_existed") == 0


def test_clear_when_root_doesnt_exist(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "nada"))
    assert cache.clear() == 0


def test_set_creates_intermediate_dirs() -> None:
    cache.set_("deeply/nested", "key", "val", ttl_seconds=60)
    # The namespace gets sanitized to only alnum + hyphen/underscore
    assert cache.get("deeply/nested", "key") == "val"


def test_corrupt_file_returns_none_oserror(tmp_path, monkeypatch) -> None:
    """Test the broad except OSError branch on read failure."""
    cache.set_("ns", "key", "val", ttl_seconds=60)
    # Make the file unreadable by replacing with a directory (OSError on read)
    files = list((tmp_path / "brasil-mcp" / "lookups" / "ns").glob("*.json"))
    assert files
    f = files[0]
    f.unlink()
    f.mkdir()
    assert cache.get("ns", "key") is None


def test_default_now_uses_current_time() -> None:
    """Smoke: when now is None, uses time.time()."""
    start = time.time()
    cache.set_("ns", "k", "v", ttl_seconds=60)
    assert cache.get("ns", "k") == "v"  # should hit (not expired)
    # Just to exercise the default-now branch
    assert time.time() >= start


def test_clear_namespace_that_doesnt_exist_when_root_does() -> None:
    """Root exists (created by prior set_), but specific namespace never used."""
    cache.set_("existing_ns", "k", "v", ttl_seconds=60)
    # Now query clear() on a namespace that was never written
    assert cache.clear("never_written") == 0
