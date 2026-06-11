from __future__ import annotations

from typing import Any

from opendata_sdk._config import DEFAULT_BASE_URL, ClientConfig
from opendata_sdk._query import Query
from opendata_sdk._resources.categories import AsyncCategoryResource
from opendata_sdk._resources.datasets import AsyncDatasetResource
from opendata_sdk._resources.providers import AsyncProviderResource
from opendata_sdk._resources.search import AsyncSearchResource
from opendata_sdk._resources.sql import AsyncSqlResource
from opendata_sdk._result import DataResult
from opendata_sdk._transport import AsyncTransport
from opendata_sdk._types import DatasetMeta, SearchResponse, SuggestResponse


class OpenData:
    """Asynchronous OpenData API client.

    Usage::

        from opendata_sdk.aio import OpenData

        async with OpenData(api_key="od_live_...") as client:
            df = await client.load("bls/cpi-u")
            df = df.to_pandas()
    """

    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str | None = None,
        timeout: float = 30.0,
        max_retries: int = 3,
    ) -> None:
        config = ClientConfig(
            base_url=base_url or DEFAULT_BASE_URL,
            api_key=api_key,
            timeout=timeout,
            max_retries=max_retries,
        )
        self._transport = AsyncTransport(config)
        self._datasets = AsyncDatasetResource(self._transport)
        self._providers = AsyncProviderResource(self._transport)
        self._categories = AsyncCategoryResource(self._transport)
        self._search = AsyncSearchResource(self._transport)
        self._sql = AsyncSqlResource(self._transport)

    @property
    def datasets(self) -> AsyncDatasetResource:
        """Dataset operations: list, get, query, create, update, delete."""
        return self._datasets

    @property
    def providers(self) -> AsyncProviderResource:
        """Provider operations: list, get."""
        return self._providers

    @property
    def categories(self) -> AsyncCategoryResource:
        """Category operations: list, get."""
        return self._categories

    @property
    def sql(self) -> AsyncSqlResource:
        """SQL query operations."""
        return self._sql

    async def meta(self, path: str) -> DatasetMeta:
        """Get full metadata for a dataset. Shortcut for client.datasets.get()."""
        return await self._datasets.get(path)

    async def query(self, path: str, query: Query | None = None, **kwargs: Any) -> DataResult:
        """Query a dataset and return the first page. Shortcut for client.datasets.query()."""
        return await self._datasets.query(path, query, **kwargs)

    async def load(
        self,
        path: str,
        query: Query | None = None,
        *,
        max_rows: int | None = None,
    ) -> DataResult:
        """Load a full dataset, auto-paginating across all pages.

        Shortcut for client.datasets.query_all(). The name ``load`` signals
        that all data is fetched into memory -- use ``client.datasets.query_iter()``
        for large datasets that don't fit in memory.

        Example::

            df = await client.load("bls/cpi-u")
            df = df.to_pandas()
        """
        return await self._datasets.query_all(path, query, max_rows=max_rows)

    async def search(self, q: str, **kwargs: Any) -> SearchResponse:
        """Search datasets. Shortcut for the search resource."""
        return await self._search.search(q, **kwargs)

    async def suggest(self, q: str, **kwargs: Any) -> SuggestResponse:
        """Autocomplete suggestions. Shortcut for the search resource."""
        return await self._search.suggest(q, **kwargs)

    async def close(self) -> None:
        """Close the underlying HTTP transport."""
        await self._transport.close()

    async def __aenter__(self) -> OpenData:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()

    def __repr__(self) -> str:
        return f"OpenData(base_url={self._transport._config.base_url!r}, async=True)"
