"""Tests for the shared httpx wrapper."""

from __future__ import annotations

import httpx
import pytest

from brasil_mcp.core.lookups.http_client import (
    NetworkError,
    NotFoundError,
    UpstreamError,
    get_json,
)


def _make_client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler), timeout=2.0)


def test_get_json_success():
    def handler(req):
        return httpx.Response(200, json={"ok": True})

    with _make_client(handler) as c:
        assert get_json("http://x/a", client=c) == {"ok": True}


def test_get_json_404_raises_notfound():
    def handler(req):
        return httpx.Response(404)

    with _make_client(handler) as c, pytest.raises(NotFoundError):
        get_json("http://x/a", client=c)


def test_get_json_500_retries_then_fails():
    calls = {"n": 0}

    def handler(req):
        calls["n"] += 1
        return httpx.Response(500)

    with _make_client(handler) as c, pytest.raises(NetworkError):
        get_json("http://x/a", client=c, retries=2)
    assert calls["n"] == 3  # initial + 2 retries


def test_get_json_timeout_retries(monkeypatch):
    calls = {"n": 0}

    def handler(req):
        calls["n"] += 1
        raise httpx.ConnectError("simulated")

    # Stub sleep to avoid actual backoff
    monkeypatch.setattr("brasil_mcp.core.lookups.http_client.time.sleep", lambda x: None)

    with _make_client(handler) as c, pytest.raises(NetworkError):
        get_json("http://x/a", client=c, retries=1)
    assert calls["n"] == 2


def test_get_json_500_then_200(monkeypatch):
    """Retry succeeds on second attempt."""
    calls = {"n": 0}

    def handler(req):
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(500)
        return httpx.Response(200, json={"ok": "now"})

    monkeypatch.setattr("brasil_mcp.core.lookups.http_client.time.sleep", lambda x: None)

    with _make_client(handler) as c:
        result = get_json("http://x/a", client=c, retries=2)
    assert result == {"ok": "now"}
    assert calls["n"] == 2


def test_get_json_4xx_non_404_raises_upstream():
    def handler(req):
        return httpx.Response(403, text="forbidden")

    with _make_client(handler) as c, pytest.raises(UpstreamError) as exc:
        get_json("http://x/a", client=c)
    assert exc.value.status_code == 403


def test_get_json_invalid_json_raises_upstream():
    def handler(req):
        return httpx.Response(200, text="not json {{{")

    with _make_client(handler) as c, pytest.raises(UpstreamError):
        get_json("http://x/a", client=c)


def test_get_json_with_params():
    captured = {}

    def handler(req):
        captured["url"] = str(req.url)
        return httpx.Response(200, json={})

    with _make_client(handler) as c:
        get_json("http://x/a", params={"foo": "bar"}, client=c)
    assert "foo=bar" in captured["url"]


def test_get_json_own_client_path(monkeypatch):
    """When client=None, function creates its own client and closes it."""
    # Use a transport-level monkeypatch on httpx.Client itself
    import brasil_mcp.core.lookups.http_client as mod

    closed = {"yes": False}
    original = httpx.Client

    class FakeClient(original):
        def __init__(self, *a, **k):
            super().__init__(
                *a, **k, transport=httpx.MockTransport(lambda r: httpx.Response(200, json={"x": 1}))
            )

        def close(self):
            closed["yes"] = True
            super().close()

    monkeypatch.setattr(mod, "httpx", httpx)  # ensure same reference

    # Force the own_client path by passing client=None — but we can't easily intercept
    # the httpx.Client(...) constructor inside. Instead, just verify the function works
    # by calling it without a custom client.
    monkeypatch.setattr(mod.httpx, "Client", FakeClient)
    result = get_json("http://x/a")
    assert result == {"x": 1}
    assert closed["yes"] is True
