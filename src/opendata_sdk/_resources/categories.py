from __future__ import annotations

from opendata_sdk._transport import AsyncTransport, SyncTransport
from opendata_sdk._types import Category


class CategoryResource:
    """Sync category operations."""

    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport

    def list(self) -> list[Category]:
        """List all dataset categories."""
        resp = self._transport.request("GET", "/categories")
        data = resp.json()
        items = data if isinstance(data, list) else data.get("items", data.get("categories", []))
        return [Category.model_validate(c) for c in items]

    def get(self, slug: str) -> Category:
        """Get a single category by slug."""
        resp = self._transport.request("GET", f"/categories/{slug}")
        return Category.model_validate(resp.json())


class AsyncCategoryResource:
    """Async category operations."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    async def list(self) -> list[Category]:
        """List all dataset categories."""
        resp = await self._transport.request("GET", "/categories")
        data = resp.json()
        items = data if isinstance(data, list) else data.get("items", data.get("categories", []))
        return [Category.model_validate(c) for c in items]

    async def get(self, slug: str) -> Category:
        """Get a single category by slug."""
        resp = await self._transport.request("GET", f"/categories/{slug}")
        return Category.model_validate(resp.json())
