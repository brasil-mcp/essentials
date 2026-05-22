"""Shared httpx wrapper for lookup tools.

Standardized:
- User-Agent identifying brasil-mcp + version.
- 10s default timeout, retry with exponential backoff on transient errors.
- All network errors get raised as `LookupError` subclasses (defined here)
  so each lookup module returns a uniform error shape.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import httpx

import brasil_mcp

DEFAULT_TIMEOUT_SECONDS = 10.0
DEFAULT_RETRIES = 2  # so total attempts = 3 (initial + 2 retries)
RETRY_BACKOFF_SECONDS = 0.5

USER_AGENT = (
    f"brasil-mcp-essentials/{brasil_mcp.__version__} (+https://github.com/brasil-mcp/essentials)"
)


class LookupError(Exception):
    """Base class for lookup errors."""


class NotFoundError(LookupError):
    """The remote service responded with 404 (resource doesn't exist)."""


class NetworkError(LookupError):
    """Connection failure / timeout / server error after retries exhausted."""


class UpstreamError(LookupError):
    """The remote returned a non-success status that isn't a 404."""

    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(f"upstream returned {status_code}: {message}")
        self.status_code = status_code


@dataclass(frozen=True, slots=True)
class HttpResponse:
    status_code: int
    body: Any  # parsed JSON or text


def get_json(
    url: str,
    *,
    params: dict[str, str] | None = None,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    retries: int = DEFAULT_RETRIES,
    client: httpx.Client | None = None,
) -> Any:
    """GET a URL and return the parsed JSON body.

    Raises NotFoundError on 404. Raises NetworkError after retries exhausted on
    timeout / connect error / 5xx. Raises UpstreamError for other 4xx.
    """
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    own_client = client is None
    if client is None:
        client = httpx.Client(timeout=timeout, follow_redirects=True, headers=headers)
    try:
        last_exc: Exception | None = None
        for attempt in range(retries + 1):
            try:
                resp = client.get(url, params=params)
            except (httpx.TimeoutException, httpx.ConnectError) as exc:
                last_exc = exc
                if attempt < retries:
                    time.sleep(RETRY_BACKOFF_SECONDS * (2**attempt))
                    continue
                raise NetworkError(f"network failure after {retries + 1} attempts: {exc}") from exc

            if resp.status_code == 404:
                raise NotFoundError(f"not found: {url}")
            if 500 <= resp.status_code < 600:
                if attempt < retries:
                    time.sleep(RETRY_BACKOFF_SECONDS * (2**attempt))
                    continue
                raise NetworkError(f"upstream {resp.status_code} after {retries + 1} attempts")
            if not (200 <= resp.status_code < 300):
                raise UpstreamError(resp.status_code, resp.text[:200])
            try:
                return resp.json()
            except ValueError as exc:
                raise UpstreamError(resp.status_code, f"invalid JSON: {exc}") from exc

        # Defensive — loop should always exit via return/raise above.
        raise NetworkError(  # pragma: no cover
            f"unexpected end of retry loop: {last_exc}"
        )
    finally:
        if own_client:
            client.close()
