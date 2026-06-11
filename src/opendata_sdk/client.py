from __future__ import annotations

from typing import Any

from opendata_sdk._config import DEFAULT_BASE_URL, ClientConfig
from opendata_sdk._query import Query
from opendata_sdk._resources.categories import CategoryResource
from opendata_sdk._resources.datasets import DatasetResource
from opendata_sdk._resources.providers import ProviderResource
from opendata_sdk._resources.search import SearchResource
from opendata_sdk._resources.sql import SqlResource
from opendata_sdk._result import DataResult
from opendata_sdk._transport import SyncTransport
from opendata_sdk._types import DatasetMeta, SearchResponse, SuggestResponse


class OpenData:
    """Synchronous OpenData API client.

    Usage::

        from opendata_sdk import OpenData

        client = OpenData(api_key="od_live_...")
        for dataset in client.datasets.list():
            print(dataset.name)

        df = client.load("bls/cpi-u").to_pandas()

    Or as a context manager::

        with OpenData() as client:
            results = client.search("inflation")
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
        self._transport = SyncTransport(config)
        self._datasets = DatasetResource(self._transport)
        self._providers = ProviderResource(self._transport)
        self._categories = CategoryResource(self._transport)
        self._search = SearchResource(self._transport)
        self._sql = SqlResource(self._transport)

    @property
    def datasets(self) -> DatasetResource:
        """Dataset operations: list, get, query, create, update, delete."""
        return self._datasets

    @property
    def providers(self) -> ProviderResource:
        """Provider operations: list, get."""
        return self._providers

    @property
    def categories(self) -> CategoryResource:
        """Category operations: list, get."""
        return self._categories

    @property
    def sql(self) -> SqlResource:
        """SQL query operations."""
        return self._sql

    def meta(self, path: str) -> DatasetMeta:
        """Get full metadata for a dataset. Shortcut for client.datasets.get()."""
        return self._datasets.get(path)

    def query(self, path: str, query: Query | None = None, **kwargs: Any) -> DataResult:
        """Query a dataset and return the first page. Shortcut for client.datasets.query()."""
        return self._datasets.query(path, query, **kwargs)

    def load(
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

            df = client.load("bls/cpi-u").to_pandas()
            df = client.load("bls/cpi-u", Query().filter("year", "gte", 2020)).to_pandas()
        """
        return self._datasets.query_all(path, query, max_rows=max_rows)

    def search(self, q: str, **kwargs: Any) -> SearchResponse:
        """Search datasets. Shortcut for the search resource."""
        return self._search.search(q, **kwargs)

    def suggest(self, q: str, **kwargs: Any) -> SuggestResponse:
        """Autocomplete suggestions. Shortcut for the search resource."""
        return self._search.suggest(q, **kwargs)

    def close(self) -> None:
        """Close the underlying HTTP transport."""
        self._transport.close()

    def __enter__(self) -> OpenData:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def __repr__(self) -> str:
        return f"OpenData(base_url={self._transport._config.base_url!r})"
