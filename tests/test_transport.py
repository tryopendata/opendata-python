from __future__ import annotations

import os
from unittest.mock import patch

import httpx
import pytest
import respx

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
from opendata_sdk._transport import AsyncTransport, SyncTransport

BASE = "https://api.tryopendata.ai/v1"


def _config(api_key: str | None = "sk-test", max_retries: int = 0) -> ClientConfig:
    return ClientConfig(base_url=BASE, api_key=api_key, timeout=5.0, max_retries=max_retries)


# ── Auth header ──────────────────────────────────────────────────────


@respx.mock
def test_auth_header_sent():
    route = respx.get(f"{BASE}/test").mock(return_value=httpx.Response(200, json={}))
    transport = SyncTransport(_config(api_key="sk-secret"))
    transport.request("GET", "/test")
    assert route.calls.last.request.headers["X-API-Key"] == "sk-secret"
    transport.close()


@respx.mock
def test_no_auth_header_when_none():
    route = respx.get(f"{BASE}/test").mock(return_value=httpx.Response(200, json={}))
    with patch.dict(os.environ, {}, clear=True):
        config = ClientConfig(base_url=BASE, api_key=None, timeout=5.0, max_retries=0)
        transport = SyncTransport(config)
        transport.request("GET", "/test")
        assert "X-API-Key" not in route.calls.last.request.headers
        transport.close()


# ── User-Agent ───────────────────────────────────────────────────────


@respx.mock
def test_user_agent_present():
    route = respx.get(f"{BASE}/test").mock(return_value=httpx.Response(200, json={}))
    transport = SyncTransport(_config())
    transport.request("GET", "/test")
    ua = route.calls.last.request.headers["User-Agent"]
    assert "opendata-sdk/" in ua
    assert "python/" in ua
    transport.close()


# ── HTTP error mapping ───────────────────────────────────────────────


@respx.mock
def test_401_raises_authentication_error():
    respx.get(f"{BASE}/test").mock(
        return_value=httpx.Response(401, json={"detail": "Invalid API key"})
    )
    transport = SyncTransport(_config())
    with pytest.raises(AuthenticationError, match="Invalid API key"):
        transport.request("GET", "/test")
    transport.close()


@respx.mock
def test_403_raises_forbidden_error():
    respx.get(f"{BASE}/test").mock(return_value=httpx.Response(403, json={"detail": "Forbidden"}))
    transport = SyncTransport(_config())
    with pytest.raises(ForbiddenError):
        transport.request("GET", "/test")
    transport.close()


@respx.mock
def test_404_raises_not_found():
    respx.get(f"{BASE}/test").mock(return_value=httpx.Response(404, json={"detail": "Not found"}))
    transport = SyncTransport(_config())
    with pytest.raises(NotFoundError):
        transport.request("GET", "/test")
    transport.close()


@respx.mock
def test_429_raises_rate_limit_with_retry_after():
    respx.get(f"{BASE}/test").mock(
        return_value=httpx.Response(
            429,
            json={"detail": "Too many requests"},
            headers={"retry-after": "30"},
        )
    )
    transport = SyncTransport(_config())
    with pytest.raises(RateLimitError) as exc_info:
        transport.request("GET", "/test")
    assert exc_info.value.retry_after == 30.0
    transport.close()


@respx.mock
def test_400_raises_invalid_request_error():
    respx.get(f"{BASE}/test").mock(return_value=httpx.Response(400, json={"detail": "Bad request"}))
    transport = SyncTransport(_config())
    with pytest.raises(InvalidRequestError):
        transport.request("GET", "/test")
    transport.close()


@respx.mock
def test_422_raises_invalid_request_error():
    respx.get(f"{BASE}/test").mock(
        return_value=httpx.Response(422, json={"detail": "Unprocessable"})
    )
    transport = SyncTransport(_config())
    with pytest.raises(InvalidRequestError):
        transport.request("GET", "/test")
    transport.close()


@respx.mock
def test_500_raises_api_error():
    respx.get(f"{BASE}/test").mock(
        return_value=httpx.Response(500, json={"detail": "Internal error"})
    )
    transport = SyncTransport(_config())
    with pytest.raises(APIError):
        transport.request("GET", "/test")
    transport.close()


# ── Retry behavior ───────────────────────────────────────────────────


@respx.mock
def test_retry_on_503_for_get():
    """GET should retry on 503, then succeed on 200."""
    route = respx.get(f"{BASE}/test").mock(
        side_effect=[
            httpx.Response(503),
            httpx.Response(200, json={"ok": True}),
        ]
    )
    transport = SyncTransport(_config(max_retries=2))
    with patch("time.sleep"):  # skip actual delay
        resp = transport.request("GET", "/test")
    assert resp.status_code == 200
    assert route.call_count == 2
    transport.close()


@respx.mock
def test_no_retry_on_503_for_post():
    """POST should NOT retry on 503 -- just raise immediately."""
    respx.post(f"{BASE}/test").mock(
        return_value=httpx.Response(503, json={"detail": "Unavailable"})
    )
    transport = SyncTransport(_config(max_retries=2))
    with pytest.raises(APIError):
        transport.request("POST", "/test")
    transport.close()


# ── Connection / timeout errors ──────────────────────────────────────


@respx.mock
def test_connect_error_raises_api_connection_error():
    respx.get(f"{BASE}/test").mock(side_effect=httpx.ConnectError("refused"))
    transport = SyncTransport(_config())
    with pytest.raises(APIConnectionError, match="Connection error"):
        transport.request("GET", "/test")
    transport.close()


@respx.mock
def test_timeout_raises_api_connection_error():
    respx.get(f"{BASE}/test").mock(side_effect=httpx.ReadTimeout("timed out"))
    transport = SyncTransport(_config())
    with pytest.raises(APIConnectionError, match="timed out"):
        transport.request("GET", "/test")
    transport.close()


# ── Context manager ──────────────────────────────────────────────────


@respx.mock
def test_sync_transport_context_manager():
    respx.get(f"{BASE}/test").mock(return_value=httpx.Response(200, json={}))
    with SyncTransport(_config()) as transport:
        resp = transport.request("GET", "/test")
        assert resp.status_code == 200


# ── Async transport ──────────────────────────────────────────────────


@respx.mock
async def test_async_auth_header_sent():
    route = respx.get(f"{BASE}/test").mock(return_value=httpx.Response(200, json={}))
    transport = AsyncTransport(_config(api_key="sk-async"))
    await transport.request("GET", "/test")
    assert route.calls.last.request.headers["X-API-Key"] == "sk-async"
    await transport.close()


@respx.mock
async def test_async_401_raises_authentication_error():
    respx.get(f"{BASE}/test").mock(return_value=httpx.Response(401, json={"detail": "Nope"}))
    transport = AsyncTransport(_config())
    with pytest.raises(AuthenticationError):
        await transport.request("GET", "/test")
    await transport.close()


@respx.mock
async def test_async_retry_on_503():
    route = respx.get(f"{BASE}/test").mock(
        side_effect=[
            httpx.Response(503),
            httpx.Response(200, json={"ok": True}),
        ]
    )
    transport = AsyncTransport(_config(max_retries=2))
    with patch("asyncio.sleep", return_value=None):
        resp = await transport.request("GET", "/test")
    assert resp.status_code == 200
    assert route.call_count == 2
    await transport.close()


@respx.mock
async def test_async_no_retry_for_post():
    respx.post(f"{BASE}/test").mock(return_value=httpx.Response(503, json={"detail": "down"}))
    transport = AsyncTransport(_config(max_retries=2))
    with pytest.raises(APIError):
        await transport.request("POST", "/test")
    await transport.close()


@respx.mock
async def test_async_connect_error():
    respx.get(f"{BASE}/test").mock(side_effect=httpx.ConnectError("refused"))
    transport = AsyncTransport(_config())
    with pytest.raises(APIConnectionError):
        await transport.request("GET", "/test")
    await transport.close()


@respx.mock
async def test_async_timeout_error():
    respx.get(f"{BASE}/test").mock(side_effect=httpx.ReadTimeout("timed out"))
    transport = AsyncTransport(_config())
    with pytest.raises(APIConnectionError):
        await transport.request("GET", "/test")
    await transport.close()


@respx.mock
async def test_async_context_manager():
    respx.get(f"{BASE}/test").mock(return_value=httpx.Response(200, json={}))
    async with AsyncTransport(_config()) as transport:
        resp = await transport.request("GET", "/test")
        assert resp.status_code == 200


# ── Error body parsing ───────────────────────────────────────────────


@respx.mock
def test_error_body_preserved():
    body = {"detail": "Not found", "code": "DATASET_NOT_FOUND"}
    respx.get(f"{BASE}/test").mock(return_value=httpx.Response(404, json=body))
    transport = SyncTransport(_config())
    with pytest.raises(NotFoundError) as exc_info:
        transport.request("GET", "/test")
    assert exc_info.value.body == body
    assert exc_info.value.status_code == 404
    transport.close()


@respx.mock
def test_error_message_from_list_detail_invalid_request():
    """Error body with detail as a list should use the first item."""
    body = {"detail": ["Field required", "Invalid format"]}
    respx.get(f"{BASE}/test").mock(return_value=httpx.Response(422, json=body))
    transport = SyncTransport(_config())
    with pytest.raises(InvalidRequestError, match="Field required"):
        transport.request("GET", "/test")
    transport.close()


@respx.mock
def test_error_fallback_to_text():
    """Non-JSON error body should still produce a message."""
    respx.get(f"{BASE}/test").mock(return_value=httpx.Response(500, text="Internal Server Error"))
    transport = SyncTransport(_config())
    with pytest.raises(APIError, match="Internal Server Error"):
        transport.request("GET", "/test")
    transport.close()


@respx.mock
def test_request_id_propagated():
    respx.get(f"{BASE}/test").mock(
        return_value=httpx.Response(
            500,
            json={"detail": "fail"},
            headers={"x-request-id": "req-abc-123"},
        )
    )
    transport = SyncTransport(_config())
    with pytest.raises(APIError) as exc_info:
        transport.request("GET", "/test")
    assert exc_info.value.request_id == "req-abc-123"
    transport.close()
