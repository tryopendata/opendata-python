from __future__ import annotations

from typing import Any


class OpenDataError(Exception):
    """Base exception for OpenData SDK."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        request_id: str | None = None,
        body: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.request_id = request_id
        self.body = body


class APIError(OpenDataError):
    """Server-side error (5xx). The API is having trouble. GET requests are retried."""

    def __str__(self) -> str:
        parts = [self.message]
        if self.request_id:
            parts.append(f"Request ID: {self.request_id}")
        return "\n".join(parts)


class APIConnectionError(OpenDataError):
    """Network or timeout error. The request never reached the server (or never came back)."""

    def __str__(self) -> str:
        parts = [self.message]
        if "timed out" in self.message.lower():
            parts.append("To increase the timeout: OpenData(timeout=60.0)")
        else:
            parts.append("Check your network connection and that the API is reachable.")
        return "\n".join(parts)


class AuthenticationError(OpenDataError):
    """Invalid or missing API key (401)."""

    def __str__(self) -> str:
        parts = [self.message]
        parts.append(
            "Pass your key: OpenData(api_key='od_live_...')\n"
            "Or set the env var: export OPENDATA_API_KEY='od_live_...'\n"
            "Get a key at: https://tryopendata.ai/settings/api-keys"
        )
        return "\n".join(parts)


class ForbiddenError(OpenDataError):
    """Insufficient permissions (403). Your key doesn't have access to this resource."""

    def __str__(self) -> str:
        parts = [self.message]
        parts.append(
            "Your API key doesn't have access to this resource. "
            "Check your plan or contact support at https://tryopendata.ai"
        )
        return "\n".join(parts)


class NotFoundError(OpenDataError):
    """Resource not found (404). The dataset path or endpoint doesn't exist."""

    def __str__(self) -> str:
        parts = [self.message]
        parts.append(
            "Dataset paths use 'provider/dataset' format, e.g. 'bls/cpi-u'.\n"
            "Find datasets with: client.search('your topic')"
        )
        return "\n".join(parts)


class RateLimitError(OpenDataError):
    """Too many requests (429). The SDK retries GET requests automatically with backoff."""

    def __init__(
        self,
        message: str,
        retry_after: float | None = None,
        **kwargs: object,
    ) -> None:
        super().__init__(message, **kwargs)  # type: ignore[arg-type]
        self.retry_after = retry_after
        self.upgrade_message: str | None = None
        if self.body and isinstance(self.body, dict):
            self.upgrade_message = self.body.get("upgrade_message")

    def __str__(self) -> str:
        parts = [self.message]
        if self.retry_after is not None:
            parts.append(f"Retry after {self.retry_after:.0f}s.")
        if self.upgrade_message:
            parts.append(self.upgrade_message)
        parts.append(
            "Add an API key for higher limits: OpenData(api_key='od_live_...')\n"
            "Create a free account (no credit card required): https://tryopendata.ai/settings/api-keys"
        )
        return "\n".join(parts)


class InvalidRequestError(OpenDataError):
    """Invalid request parameters (400/422). The query or payload has a problem."""

    def __str__(self) -> str:
        parts = [self.message]
        parts.append(
            "If a column name is wrong, names must be lowercase with underscores "
            "(e.g. 'state_code', not 'StateCode').\n"
            "Use client.meta('provider/dataset') to see available columns and their types."
        )
        return "\n".join(parts)
