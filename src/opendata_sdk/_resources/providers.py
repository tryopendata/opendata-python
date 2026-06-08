from __future__ import annotations

from opendata_sdk._pagination import AsyncPaginatedList, PaginatedList
from opendata_sdk._transport import AsyncTransport, SyncTransport
from opendata_sdk._types import Provider


class ProviderResource:
    """Sync provider operations."""

    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport

    def list(self, *, limit: int = 20, offset: int = 0) -> PaginatedList[Provider]:
        """List data providers with auto-pagination."""
        params: dict[str, str] = {"limit": str(limit), "offset": str(offset)}
        resp = self._transport.request("GET", "/providers", params=params)
        data = resp.json()
        items_raw = data.get("items", [])
        total = data.get("total", len(items_raw))
        items = [Provider.model_validate(p) for p in items_raw]

        def fetch_next(lim: int, off: int) -> tuple[list[Provider], int]:
            p = {"limit": str(lim), "offset": str(off)}
            r = self._transport.request("GET", "/providers", params=p)
            d = r.json()
            raw = d.get("items", [])
            return [Provider.model_validate(x) for x in raw], d.get("total", len(raw))

        return PaginatedList(items, total, fetch_next, limit, offset)

    def get(self, slug: str) -> Provider:
        """Get a single provider by slug."""
        resp = self._transport.request("GET", f"/providers/{slug}")
        return Provider.model_validate(resp.json())


class AsyncProviderResource:
    """Async provider operations."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    async def list(self, *, limit: int = 20, offset: int = 0) -> AsyncPaginatedList[Provider]:
        """List data providers with auto-pagination."""
        params: dict[str, str] = {"limit": str(limit), "offset": str(offset)}
        resp = await self._transport.request("GET", "/providers", params=params)
        data = resp.json()
        items_raw = data.get("items", [])
        total = data.get("total", len(items_raw))
        items = [Provider.model_validate(p) for p in items_raw]

        async def fetch_next(lim: int, off: int) -> tuple[list[Provider], int]:
            p = {"limit": str(lim), "offset": str(off)}
            r = await self._transport.request("GET", "/providers", params=p)
            d = r.json()
            raw = d.get("items", [])
            return [Provider.model_validate(x) for x in raw], d.get("total", len(raw))

        return AsyncPaginatedList(items, total, fetch_next, limit, offset)

    async def get(self, slug: str) -> Provider:
        """Get a single provider by slug."""
        resp = await self._transport.request("GET", f"/providers/{slug}")
        return Provider.model_validate(resp.json())
