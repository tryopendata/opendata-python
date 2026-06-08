from __future__ import annotations

import logging
import platform
import random
import sys
import time
from typing import Any

import httpx

from opendata_sdk._config import ClientConfig
from opendata_sdk._exceptions import (
    APIConnectionError,
    APIError,
    AuthenticationError,
    ForbiddenError,
    InvalidRequestError,
    NotFoundError,
    RateLimitError,
)
from opendata_sdk._version import __version__

logger = logging.getLogger("opendata_sdk")

# Methods that are safe to retry (idempotent)
_RETRYABLE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})

# Status codes worth retrying
_RETRYABLE_STATUSES = frozenset({429, 500, 502, 503, 504})


def _user_agent() -> str:
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    system = platform.system().lower()
    machine = platform.machine()
    return f"opendata-sdk/{__version__} python/{py_version} {system}/{machine}"


def _parse_error_message(response: httpx.Response) -> str:
    """Extract a human-readable error message from the response body."""
    try:
        body = response.json()
        if isinstance(body, dict):
            # Try common error body shapes
            for key in ("detail", "message", "error"):
                if key in body:
                    val = body[key]
                    if isinstance(val, str):
                        return val
                    if isinstance(val, list) and val:
                        return str(val[0])
                    return str(val)
        return response.text
    except Exception:
        return response.text or f"HTTP {response.status_code}"


def _parse_error_body(response: httpx.Response) -> dict[str, Any] | None:
    """Parse the JSON error body, or return None."""
    try:
        body = response.json()
        return body if isinstance(body, dict) else None
    except Exception:
        return None


def _raise_for_status(response: httpx.Response) -> None:
    """Map HTTP status codes to SDK exceptions."""
    status = response.status_code
    if 200 <= status < 300:
        return

    message = _parse_error_message(response)
    body = _parse_error_body(response)
    request_id = response.headers.get("x-request-id")

    common = {"status_code": status, "request_id": request_id, "body": body}

    if status == 401:
        raise AuthenticationError(message, **common)
    if status == 403:
        raise ForbiddenError(message, **common)
    if status == 404:
        raise NotFoundError(message, **common)
    if status == 429:
        retry_after_raw = response.headers.get("retry-after")
        retry_after = float(retry_after_raw) if retry_after_raw else None
        raise RateLimitError(message, retry_after=retry_after, **common)
    if status in (400, 422):
        raise InvalidRequestError(message, **common)
    if status >= 500:
        raise APIError(message, **common)

    # Catch-all for unexpected 4xx
    raise APIError(message, **common)


def _backoff_delay(attempt: int, retry_after: float | None = None) -> float:
    """Exponential backoff with jitter. Respects Retry-After if provided."""
    if retry_after is not None and retry_after > 0:
        return retry_after
    base = min(2.0**attempt, 30.0)
    jitter = random.uniform(0, base * 0.5)  # noqa: S311
    return base + jitter


class SyncTransport:
    """Synchronous HTTP transport wrapping httpx.Client."""

    def __init__(self, config: ClientConfig) -> None:
        self._config = config
        headers: dict[str, str] = {
            "User-Agent": _user_agent(),
            "Accept": "application/json",
        }
        if config.api_key:
            headers["X-API-Key"] = config.api_key

        self._client = httpx.Client(
            base_url=config.base_url,
            headers=headers,
            timeout=config.timeout,
        )

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> httpx.Response:
        """Send an HTTP request with retry logic for safe methods."""
        method_upper = method.upper()
        can_retry = method_upper in _RETRYABLE_METHODS
        max_attempts = self._config.max_retries + 1 if can_retry else 1

        last_exc: Exception | None = None
        for attempt in range(max_attempts):
            try:
                response = self._client.request(
                    method_upper,
                    path,
                    params=params,
                    json=json_body,
                )
            except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
                last_exc = exc
                if not can_retry or attempt >= max_attempts - 1:
                    raise APIConnectionError(
                        f"Connection error: {exc}",
                        status_code=None,
                        request_id=None,
                    ) from exc
                time.sleep(_backoff_delay(attempt))
                continue
            except httpx.TimeoutException as exc:
                last_exc = exc
                if not can_retry or attempt >= max_attempts - 1:
                    raise APIConnectionError(
                        f"Request timed out after {self._config.timeout}s",
                        status_code=None,
                        request_id=None,
                    ) from exc
                time.sleep(_backoff_delay(attempt))
                continue

            # Check for retryable status codes
            is_retryable = response.status_code in _RETRYABLE_STATUSES
            if can_retry and is_retryable and attempt < max_attempts - 1:
                retry_after_raw = response.headers.get("retry-after")
                retry_after = float(retry_after_raw) if retry_after_raw else None
                time.sleep(_backoff_delay(attempt, retry_after))
                continue

            _raise_for_status(response)
            return response

        # Should not get here, but just in case
        if last_exc:
            raise APIConnectionError(
                f"Request failed after {max_attempts} attempts: {last_exc}",
                status_code=None,
                request_id=None,
            ) from last_exc
        raise APIConnectionError(
            f"Request failed after {max_attempts} attempts",
            status_code=None,
            request_id=None,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> SyncTransport:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


class AsyncTransport:
    """Asynchronous HTTP transport wrapping httpx.AsyncClient."""

    def __init__(self, config: ClientConfig) -> None:
        self._config = config
        headers: dict[str, str] = {
            "User-Agent": _user_agent(),
            "Accept": "application/json",
        }
        if config.api_key:
            headers["X-API-Key"] = config.api_key

        self._client = httpx.AsyncClient(
            base_url=config.base_url,
            headers=headers,
            timeout=config.timeout,
        )

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> httpx.Response:
        """Send an async HTTP request with retry logic for safe methods."""
        import asyncio

        method_upper = method.upper()
        can_retry = method_upper in _RETRYABLE_METHODS
        max_attempts = self._config.max_retries + 1 if can_retry else 1

        last_exc: Exception | None = None
        for attempt in range(max_attempts):
            try:
                response = await self._client.request(
                    method_upper,
                    path,
                    params=params,
                    json=json_body,
                )
            except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
                last_exc = exc
                if not can_retry or attempt >= max_attempts - 1:
                    raise APIConnectionError(
                        f"Connection error: {exc}",
                        status_code=None,
                        request_id=None,
                    ) from exc
                await asyncio.sleep(_backoff_delay(attempt))
                continue
            except httpx.TimeoutException as exc:
                last_exc = exc
                if not can_retry or attempt >= max_attempts - 1:
                    raise APIConnectionError(
                        f"Request timed out after {self._config.timeout}s",
                        status_code=None,
                        request_id=None,
                    ) from exc
                await asyncio.sleep(_backoff_delay(attempt))
                continue

            # Check for retryable status codes
            is_retryable = response.status_code in _RETRYABLE_STATUSES
            if can_retry and is_retryable and attempt < max_attempts - 1:
                retry_after_raw = response.headers.get("retry-after")
                retry_after = float(retry_after_raw) if retry_after_raw else None
                await asyncio.sleep(_backoff_delay(attempt, retry_after))
                continue

            _raise_for_status(response)
            return response

        if last_exc:
            raise APIConnectionError(
                f"Request failed after {max_attempts} attempts: {last_exc}",
                status_code=None,
                request_id=None,
            ) from last_exc
        raise APIConnectionError(
            f"Request failed after {max_attempts} attempts",
            status_code=None,
            request_id=None,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> AsyncTransport:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()
