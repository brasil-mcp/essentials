"""Shared fixtures: isolated cache + httpx mock transport factory."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import httpx
import pytest


@pytest.fixture(autouse=True)
def isolated_cache(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    yield


def make_mock_client(handler: Callable[[httpx.Request], httpx.Response]) -> httpx.Client:
    """Build an httpx.Client backed by a MockTransport. Useful for tests that
    need to control responses for arbitrary endpoints."""
    transport = httpx.MockTransport(handler)
    return httpx.Client(transport=transport, timeout=5.0, follow_redirects=True)


@pytest.fixture
def mock_transport_factory() -> Callable[[Callable[[httpx.Request], httpx.Response]], httpx.Client]:
    return make_mock_client


def json_response(payload: Any, status: int = 200) -> httpx.Response:
    return httpx.Response(status_code=status, json=payload)


@pytest.fixture
def json_response_factory():
    return json_response
