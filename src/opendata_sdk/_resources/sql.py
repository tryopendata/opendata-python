from __future__ import annotations

from typing import Any

from opendata_sdk._result import SqlResult
from opendata_sdk._sql import normalize_sql, parse_dataset_refs
from opendata_sdk._transport import AsyncTransport, SyncTransport
from opendata_sdk._types import SqlPage


class _BaseSql:
    """Shared logic for SQL query resources."""

    @staticmethod
    def _build_body(
        sql: str,
        *,
        params: list[Any] | None = None,
        timeout_ms: int | None = None,
        row_limit: int | None = None,
        view: str | None = None,
    ) -> dict[str, Any]:
        """Build the POST body for SQL query endpoints."""
        if not sql or not sql.strip():
            raise ValueError("sql must be a non-empty string")
        if len(sql) > 100_000:
            raise ValueError("sql must not exceed 100,000 characters")
        if timeout_ms is not None and not (100 <= timeout_ms <= 10000):
            raise ValueError("timeout_ms must be between 100 and 10000")
        if row_limit is not None and not (1 <= row_limit <= 10000):
            raise ValueError("row_limit must be between 1 and 10000")

        body: dict[str, Any] = {
            "sql": sql,
            "response_format": "columnar",
        }
        if params is not None:
            body["params"] = params
        if timeout_ms is not None:
            body["timeout_ms"] = timeout_ms
        if row_limit is not None:
            body["row_limit"] = row_limit
        if view is not None:
            body["view"] = view
        return body

    @staticmethod
    def _resolve_path(
        sql: str,
        dataset: str | None = None,
    ) -> tuple[str, str]:
        """Determine the API path and normalize the SQL.

        Returns (api_path, normalized_sql).
        """
        if dataset is not None:
            parts = dataset.strip("/").split("/")
            if len(parts) != 2:
                raise ValueError(f"dataset must be 'provider/dataset', got: {dataset}")
            return f"/datasets/{parts[0]}/{parts[1]}/query", sql

        refs = parse_dataset_refs(sql)
        normalized = normalize_sql(sql)

        if len(refs) == 1:
            provider, ds = refs[0]
            return f"/datasets/{provider}/{ds}/query", normalized

        return "/query", normalized

    @staticmethod
    def _parse_response(data: dict[str, Any]) -> SqlResult:
        """Parse a SQL query response into a SqlResult."""
        page = SqlPage.model_validate(data)
        data_page = page.to_data_page()
        return SqlResult(
            data_page,
            execution_time_ms=page.execution_time_ms,
            truncated=page.truncated,
            row_count=page.row_count,
            sql_warnings=page.warnings or [],
        )


class SqlResource:
    """Sync SQL query operations."""

    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport

    def execute(
        self,
        sql: str,
        *,
        params: list[Any] | None = None,
        timeout_ms: int | None = None,
        row_limit: int | None = None,
        view: str | None = None,
        dataset: str | None = None,
    ) -> SqlResult:
        """Execute a SQL query and return the result.

        The query is automatically routed to the single-dataset or
        cross-dataset endpoint based on the table references in the SQL.
        Pass ``dataset`` explicitly to force the single-dataset endpoint.
        """
        api_path, normalized_sql = _BaseSql._resolve_path(sql, dataset)
        body = _BaseSql._build_body(
            normalized_sql,
            params=params,
            timeout_ms=timeout_ms,
            row_limit=row_limit,
            view=view,
        )
        resp = self._transport.request("POST", api_path, json_body=body)
        return _BaseSql._parse_response(resp.json())


class AsyncSqlResource:
    """Async SQL query operations. Mirrors SqlResource with async methods."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    async def execute(
        self,
        sql: str,
        *,
        params: list[Any] | None = None,
        timeout_ms: int | None = None,
        row_limit: int | None = None,
        view: str | None = None,
        dataset: str | None = None,
    ) -> SqlResult:
        """Execute a SQL query and return the result.

        The query is automatically routed to the single-dataset or
        cross-dataset endpoint based on the table references in the SQL.
        Pass ``dataset`` explicitly to force the single-dataset endpoint.
        """
        api_path, normalized_sql = _BaseSql._resolve_path(sql, dataset)
        body = _BaseSql._build_body(
            normalized_sql,
            params=params,
            timeout_ms=timeout_ms,
            row_limit=row_limit,
            view=view,
        )
        resp = await self._transport.request("POST", api_path, json_body=body)
        return _BaseSql._parse_response(resp.json())
