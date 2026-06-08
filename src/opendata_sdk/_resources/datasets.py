from __future__ import annotations

import builtins
from collections.abc import AsyncIterator, Iterator
from typing import Any

from opendata_sdk._pagination import AsyncPaginatedList, PaginatedList
from opendata_sdk._query import Query
from opendata_sdk._resources._base import BaseDatasetResource
from opendata_sdk._result import DataResult
from opendata_sdk._transport import AsyncTransport, SyncTransport
from opendata_sdk._types import (
    ColumnStats,
    DataPage,
    Dataset,
    DatasetMeta,
    ViewInfo,
)


class DatasetResource:
    """Sync dataset operations."""

    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport

    def list(
        self,
        provider: str | None = None,
        *,
        limit: int = 20,
        status: str | None = None,
        sort: str | None = None,
    ) -> PaginatedList[Dataset]:
        """List datasets with auto-pagination."""
        path, params = BaseDatasetResource._build_list_params(provider, limit, 0, status, sort)
        resp = self._transport.request("GET", path, params=params)
        data = resp.json()
        items, total = BaseDatasetResource._parse_dataset_list(data)

        def fetch_next(lim: int, off: int) -> tuple[list[Dataset], int]:
            p = {**params, "limit": str(lim), "offset": str(off)}
            r = self._transport.request("GET", path, params=p)
            return BaseDatasetResource._parse_dataset_list(r.json())

        return PaginatedList(items, total, fetch_next, limit, 0)

    def get(self, path: str) -> DatasetMeta:
        """Get full metadata for a dataset."""
        provider, dataset = BaseDatasetResource._split_path(path)
        resp = self._transport.request("GET", f"/datasets/{provider}/{dataset}/meta")
        return DatasetMeta.model_validate(resp.json())

    def query(
        self,
        path: str,
        query: Query | None = None,
        **kwargs: str | int | None,
    ) -> DataResult:
        """Query dataset data. Returns a single page."""
        api_path, params = BaseDatasetResource._build_query_params(path, query, **kwargs)
        resp = self._transport.request("GET", api_path, params=params)
        return BaseDatasetResource._parse_data_result(resp.json())

    def query_all(
        self,
        path: str,
        query: Query | None = None,
        *,
        max_rows: int | None = None,
    ) -> DataResult:
        """Auto-paginate using cursor, merge all pages into one DataResult."""
        api_path, params = BaseDatasetResource._build_query_params(path, query)
        if max_rows and "limit" not in params:
            params["limit"] = str(min(max_rows, 10000))

        all_rows: builtins.list[builtins.list[Any]] = []
        total_rows: int | None = None
        columns: builtins.list[str] = []
        column_types: builtins.list[str] = []

        while True:
            resp = self._transport.request("GET", api_path, params=params)
            data = resp.json()

            if "subdatasets" in data:
                slugs = [
                    s.get("slug", s) if isinstance(s, dict) else s for s in data["subdatasets"]
                ]
                raise ValueError(
                    f"This is a hierarchical dataset with subdatasets: {slugs}. "
                    f"Query a specific subdataset instead."
                )

            page = DataPage.model_validate(data)
            if not columns:
                columns = page.columns
                column_types = page.column_types
                total_rows = page.total_rows

            all_rows.extend(page.data)

            if max_rows and len(all_rows) >= max_rows:
                all_rows = all_rows[:max_rows]
                break
            if not page.next_cursor:
                break
            params["cursor"] = page.next_cursor
            params.pop("offset", None)

        merged = DataPage(
            columns=columns,
            column_types=column_types,
            data=all_rows,
            total_rows=total_rows,
            limit=len(all_rows),
            offset=0,
        )
        return DataResult(merged)

    def query_iter(
        self,
        path: str,
        query: Query | None = None,
        *,
        page_size: int = 1000,
    ) -> Iterator[DataResult]:
        """Yield one DataResult per page for memory-efficient processing."""
        api_path, params = BaseDatasetResource._build_query_params(path, query)
        params["limit"] = str(page_size)

        while True:
            resp = self._transport.request("GET", api_path, params=params)
            result = BaseDatasetResource._parse_data_result(resp.json())
            yield result
            if not result.next_cursor:
                break
            params["cursor"] = result.next_cursor
            params.pop("offset", None)

    def columns(self, path: str, *, view: str | None = None) -> builtins.list[ColumnStats]:
        """Get column statistics for a dataset."""
        provider, dataset = BaseDatasetResource._split_path(path)
        params = {"view": view} if view else None
        resp = self._transport.request(
            "GET", f"/datasets/{provider}/{dataset}/columns", params=params
        )
        data = resp.json()
        return [ColumnStats.model_validate(c) for c in data.get("columns", [])]

    def views(self, path: str) -> builtins.list[ViewInfo]:
        """List available views for a dataset."""
        provider, dataset = BaseDatasetResource._split_path(path)
        resp = self._transport.request("GET", f"/datasets/{provider}/{dataset}/views")
        data = resp.json()
        return [ViewInfo.model_validate(v) for v in data.get("views", [])]

    def create(self, payload: dict[str, Any]) -> DatasetMeta:
        """Create a new dataset."""
        resp = self._transport.request("POST", "/datasets", json_body=payload)
        return DatasetMeta.model_validate(resp.json())

    def update(self, path: str, payload: dict[str, Any]) -> Dataset:
        """Update dataset metadata."""
        provider, dataset = BaseDatasetResource._split_path(path)
        resp = self._transport.request(
            "PATCH", f"/datasets/{provider}/{dataset}", json_body=payload
        )
        return Dataset.model_validate(resp.json())

    def delete(self, path: str) -> None:
        """Delete a dataset."""
        provider, dataset = BaseDatasetResource._split_path(path)
        self._transport.request("DELETE", f"/datasets/{provider}/{dataset}")

    def sync(self, path: str) -> None:
        """Trigger a sync for a dataset."""
        provider, dataset = BaseDatasetResource._split_path(path)
        self._transport.request("POST", f"/datasets/{provider}/{dataset}/sync")

    def related(self, path: str, *, limit: int = 8) -> builtins.list[Dataset]:
        """Get related datasets."""
        provider, dataset = BaseDatasetResource._split_path(path)
        resp = self._transport.request(
            "GET",
            f"/datasets/{provider}/{dataset}/related",
            params={"limit": str(limit)},
        )
        data = resp.json()
        results = data.get("related_datasets", data.get("results", []))
        return [Dataset.model_validate(d) for d in results]


class AsyncDatasetResource:
    """Async dataset operations. Mirrors DatasetResource with async methods."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    async def list(
        self,
        provider: str | None = None,
        *,
        limit: int = 20,
        status: str | None = None,
        sort: str | None = None,
    ) -> AsyncPaginatedList[Dataset]:
        """List datasets with auto-pagination."""
        path, params = BaseDatasetResource._build_list_params(provider, limit, 0, status, sort)
        resp = await self._transport.request("GET", path, params=params)
        data = resp.json()
        items, total = BaseDatasetResource._parse_dataset_list(data)

        async def fetch_next(lim: int, off: int) -> tuple[list[Dataset], int]:
            p = {**params, "limit": str(lim), "offset": str(off)}
            r = await self._transport.request("GET", path, params=p)
            return BaseDatasetResource._parse_dataset_list(r.json())

        return AsyncPaginatedList(items, total, fetch_next, limit, 0)

    async def get(self, path: str) -> DatasetMeta:
        """Get full metadata for a dataset."""
        provider, dataset = BaseDatasetResource._split_path(path)
        resp = await self._transport.request("GET", f"/datasets/{provider}/{dataset}/meta")
        return DatasetMeta.model_validate(resp.json())

    async def query(
        self,
        path: str,
        query: Query | None = None,
        **kwargs: str | int | None,
    ) -> DataResult:
        """Query dataset data. Returns a single page."""
        api_path, params = BaseDatasetResource._build_query_params(path, query, **kwargs)
        resp = await self._transport.request("GET", api_path, params=params)
        return BaseDatasetResource._parse_data_result(resp.json())

    async def query_all(
        self,
        path: str,
        query: Query | None = None,
        *,
        max_rows: int | None = None,
    ) -> DataResult:
        """Auto-paginate using cursor, merge all pages into one DataResult."""
        api_path, params = BaseDatasetResource._build_query_params(path, query)
        if max_rows and "limit" not in params:
            params["limit"] = str(min(max_rows, 10000))

        all_rows: builtins.list[builtins.list[Any]] = []
        total_rows: int | None = None
        columns: builtins.list[str] = []
        column_types: builtins.list[str] = []

        while True:
            resp = await self._transport.request("GET", api_path, params=params)
            data = resp.json()

            if "subdatasets" in data:
                slugs = [
                    s.get("slug", s) if isinstance(s, dict) else s for s in data["subdatasets"]
                ]
                raise ValueError(
                    f"This is a hierarchical dataset with subdatasets: {slugs}. "
                    f"Query a specific subdataset instead."
                )

            page = DataPage.model_validate(data)
            if not columns:
                columns = page.columns
                column_types = page.column_types
                total_rows = page.total_rows

            all_rows.extend(page.data)

            if max_rows and len(all_rows) >= max_rows:
                all_rows = all_rows[:max_rows]
                break
            if not page.next_cursor:
                break
            params["cursor"] = page.next_cursor
            params.pop("offset", None)

        merged = DataPage(
            columns=columns,
            column_types=column_types,
            data=all_rows,
            total_rows=total_rows,
            limit=len(all_rows),
            offset=0,
        )
        return DataResult(merged)

    async def query_iter(
        self,
        path: str,
        query: Query | None = None,
        *,
        page_size: int = 1000,
    ) -> AsyncIterator[DataResult]:
        """Yield one DataResult per page for memory-efficient processing."""
        api_path, params = BaseDatasetResource._build_query_params(path, query)
        params["limit"] = str(page_size)

        while True:
            resp = await self._transport.request("GET", api_path, params=params)
            result = BaseDatasetResource._parse_data_result(resp.json())
            yield result
            if not result.next_cursor:
                break
            params["cursor"] = result.next_cursor
            params.pop("offset", None)

    async def columns(self, path: str, *, view: str | None = None) -> builtins.list[ColumnStats]:
        """Get column statistics for a dataset."""
        provider, dataset = BaseDatasetResource._split_path(path)
        params = {"view": view} if view else None
        resp = await self._transport.request(
            "GET", f"/datasets/{provider}/{dataset}/columns", params=params
        )
        data = resp.json()
        return [ColumnStats.model_validate(c) for c in data.get("columns", [])]

    async def views(self, path: str) -> builtins.list[ViewInfo]:
        """List available views for a dataset."""
        provider, dataset = BaseDatasetResource._split_path(path)
        resp = await self._transport.request("GET", f"/datasets/{provider}/{dataset}/views")
        data = resp.json()
        return [ViewInfo.model_validate(v) for v in data.get("views", [])]

    async def create(self, payload: dict[str, Any]) -> DatasetMeta:
        """Create a new dataset."""
        resp = await self._transport.request("POST", "/datasets", json_body=payload)
        return DatasetMeta.model_validate(resp.json())

    async def update(self, path: str, payload: dict[str, Any]) -> Dataset:
        """Update dataset metadata."""
        provider, dataset = BaseDatasetResource._split_path(path)
        resp = await self._transport.request(
            "PATCH", f"/datasets/{provider}/{dataset}", json_body=payload
        )
        return Dataset.model_validate(resp.json())

    async def delete(self, path: str) -> None:
        """Delete a dataset."""
        provider, dataset = BaseDatasetResource._split_path(path)
        await self._transport.request("DELETE", f"/datasets/{provider}/{dataset}")

    async def sync(self, path: str) -> None:
        """Trigger a sync for a dataset."""
        provider, dataset = BaseDatasetResource._split_path(path)
        await self._transport.request("POST", f"/datasets/{provider}/{dataset}/sync")

    async def related(self, path: str, *, limit: int = 8) -> builtins.list[Dataset]:
        """Get related datasets."""
        provider, dataset = BaseDatasetResource._split_path(path)
        resp = await self._transport.request(
            "GET",
            f"/datasets/{provider}/{dataset}/related",
            params={"limit": str(limit)},
        )
        data = resp.json()
        results = data.get("related_datasets", data.get("results", []))
        return [Dataset.model_validate(d) for d in results]
