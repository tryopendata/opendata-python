from __future__ import annotations

from opendata_sdk._transport import AsyncTransport, SyncTransport
from opendata_sdk._types import SearchResponse, SuggestResponse


class SearchResource:
    """Sync search operations."""

    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport

    def search(
        self,
        q: str,
        *,
        mode: str | None = None,
        provider: str | None = None,
        category: str | None = None,
        sort: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> SearchResponse:
        """Full-text search across datasets."""
        params: dict[str, str] = {
            "q": q,
            "limit": str(limit),
            "offset": str(offset),
        }
        if mode:
            params["mode"] = mode
        if provider:
            params["provider"] = provider
        if category:
            params["category"] = category
        if sort:
            params["sort"] = sort
        resp = self._transport.request("GET", "/search", params=params)
        return SearchResponse.model_validate(resp.json())

    def suggest(self, q: str, *, limit: int = 5) -> SuggestResponse:
        """Autocomplete suggestions."""
        resp = self._transport.request(
            "GET", "/search/suggest", params={"q": q, "limit": str(limit)}
        )
        return SuggestResponse.model_validate(resp.json())


class AsyncSearchResource:
    """Async search operations."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    async def search(
        self,
        q: str,
        *,
        mode: str | None = None,
        provider: str | None = None,
        category: str | None = None,
        sort: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> SearchResponse:
        """Full-text search across datasets."""
        params: dict[str, str] = {
            "q": q,
            "limit": str(limit),
            "offset": str(offset),
        }
        if mode:
            params["mode"] = mode
        if provider:
            params["provider"] = provider
        if category:
            params["category"] = category
        if sort:
            params["sort"] = sort
        resp = await self._transport.request("GET", "/search", params=params)
        return SearchResponse.model_validate(resp.json())

    async def suggest(self, q: str, *, limit: int = 5) -> SuggestResponse:
        """Autocomplete suggestions."""
        resp = await self._transport.request(
            "GET", "/search/suggest", params={"q": q, "limit": str(limit)}
        )
        return SuggestResponse.model_validate(resp.json())
