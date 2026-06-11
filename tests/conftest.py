from __future__ import annotations

from typing import Any

BASE_URL = "https://api.tryopendata.ai/v1"
NOW = "2026-01-15T12:00:00Z"


def make_dataset(
    *,
    id: str = "abc-123",
    name: str = "CPI-U",
    slug: str = "cpi-u",
    path: str = "bls/cpi-u",
    provider: str = "bls",
    status: str = "ready",
    rows: int = 5000,
    **overrides: Any,
) -> dict[str, Any]:
    """Build a dataset dict matching the API shape."""
    base = {
        "id": id,
        "name": name,
        "slug": slug,
        "path": path,
        "provider": provider,
        "status": status,
        "rows": rows,
        "format": "csv",
        "star_count": 0,
        "created_at": NOW,
        "updated_at": NOW,
    }
    base.update(overrides)
    return base


def make_dataset_meta(**overrides: Any) -> dict[str, Any]:
    """Full metadata response for a dataset."""
    base = make_dataset()
    base.update(
        {
            "source_url": "https://example.com/data.csv",
            "schema_info": {"columns": []},
            "available_views": [{"name": "default"}, {"name": "timeseries"}],
            "default_view": "default",
        }
    )
    base.update(overrides)
    return base


def make_dataset_list(
    items: list[dict[str, Any]] | None = None,
    total: int | None = None,
) -> dict[str, Any]:
    """Paginated dataset list response."""
    if items is None:
        items = [make_dataset()]
    return {
        "items": items,
        "total": total if total is not None else len(items),
        "limit": 20,
        "offset": 0,
    }


def make_data_page(
    *,
    columns: list[str] | None = None,
    column_types: list[str] | None = None,
    data: list[list[Any]] | None = None,
    total_rows: int = 100,
    next_cursor: str | None = None,
) -> dict[str, Any]:
    """Columnar data response."""
    return {
        "columns": columns or ["year", "value"],
        "column_types": column_types or ["INTEGER", "DOUBLE"],
        "data": data if data is not None else [[2020, 1.5], [2021, 2.3]],
        "total_rows": total_rows,
        "filtered_rows": total_rows,
        "limit": 1000,
        "offset": 0,
        "next_cursor": next_cursor,
        "view": None,
        "warnings": [],
    }


def make_search_response(
    results: list[dict[str, Any]] | None = None,
    total: int | None = None,
) -> dict[str, Any]:
    """Search response."""
    if results is None:
        results = [
            {
                "id": "abc-123",
                "name": "CPI-U",
                "slug": "cpi-u",
                "path": "bls/cpi-u",
                "provider": "bls",
                "description": "Consumer price index",
                "status": "ready",
                "rows": 5000,
                "relevance": 0.95,
            }
        ]
    return {
        "results": results,
        "total": total if total is not None else len(results),
        "limit": 20,
        "offset": 0,
        "query": "inflation",
    }


def make_suggest_response() -> dict[str, Any]:
    return {
        "suggestions": [{"text": "inflation", "score": 0.9}],
        "query": "inf",
    }


def make_sql_page(
    *,
    columns: list[str] | None = None,
    types: list[str] | None = None,
    rows: list[list[Any]] | None = None,
    row_count: int = 2,
    execution_time_ms: float = 125.0,
    truncated: bool = False,
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    """SQL query response in columnar format."""
    return {
        "columns": columns or ["year", "value"],
        "types": types or ["INTEGER", "DOUBLE"],
        "rows": rows if rows is not None else [[2020, 1.5], [2021, 2.3]],
        "row_count": row_count,
        "execution_time_ms": execution_time_ms,
        "truncated": truncated,
        "warnings": warnings,
    }
