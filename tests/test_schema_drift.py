"""Validate SDK types against live API responses.

Fetches real responses from api.tryopendata.ai and checks that every
field the API sends is accepted by the corresponding SDK model (not
silently dropped by extra="ignore"). Catches the exact class of bug
where the API adds/renames a field and the SDK silently drops it.

Runs in CI on every push. Requires network access.
"""

from __future__ import annotations

import os
from typing import Any

import httpx
import pytest

from opendata_sdk._types import (
    Category,
    ColumnStats,
    DataPage,
    DatasetMeta,
    Provider,
    SearchResponse,
    SearchResult,
    SuggestionItem,
    SuggestResponse,
)

API_BASE = os.environ.get("OPENAPI_BASE_URL", "https://api.tryopendata.ai/v1")


@pytest.fixture(scope="module")
def client() -> httpx.Client:
    api_key = os.environ.get("OPENDATA_API_KEY", "")
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    c = httpx.Client(base_url=API_BASE, timeout=15, headers=headers)
    yield c
    c.close()


def _get_model_accepted_fields(model_cls: type) -> set[str]:
    """Field names + aliases that a Pydantic model will accept."""
    accepted: set[str] = set()
    for name, field_info in model_cls.model_fields.items():
        accepted.add(name)
        if field_info.alias:
            accepted.add(field_info.alias)
        if field_info.validation_alias and isinstance(field_info.validation_alias, str):
            accepted.add(field_info.validation_alias)
    return accepted


# Fields the SDK intentionally skips. Add sparingly with a comment.
INTENTIONAL_SKIPS: dict[str, set[str]] = {
    "SearchResult": {
        "owner",  # nested OwnerInfo, not useful in SDK
        "star_count_in_period",  # period-scoped metrics
        "query_count_in_period",
        "download_count_in_period",
    },
    "DatasetMeta": {
        "landing_page_content",  # large cached HTML blob
    },
}


def _check_coverage(
    model_cls: type,
    api_response: dict[str, Any],
    label: str,
) -> None:
    """Assert the SDK model accepts every field in the API response."""
    accepted = _get_model_accepted_fields(model_cls)
    skips = INTENTIONAL_SKIPS.get(model_cls.__name__, set())
    api_fields = set(api_response.keys())

    dropped = api_fields - accepted - skips
    if dropped:
        pytest.fail(
            f"{label}: {model_cls.__name__} drops fields from API response: "
            f"{sorted(dropped)}\n"
            f"  API sent: {sorted(api_fields)}\n"
            f"  SDK accepts: {sorted(accepted)}\n"
            f"  Add them to the SDK model or INTENTIONAL_SKIPS."
        )


def test_search_result_fields(client: httpx.Client) -> None:
    resp = client.get("/search", params={"q": "unemployment", "limit": "1"})
    resp.raise_for_status()
    data = resp.json()
    results = data.get("results", [])
    if not results:
        pytest.skip("No search results returned")

    _check_coverage(SearchResult, results[0], "GET /search")
    _check_coverage(SearchResponse, data, "GET /search (envelope)")


def test_suggest_fields(client: httpx.Client) -> None:
    resp = client.get("/search/suggest", params={"q": "cpi", "limit": "1"})
    resp.raise_for_status()
    data = resp.json()

    _check_coverage(SuggestResponse, data, "GET /search/suggest")
    suggestions = data.get("suggestions", [])
    if suggestions:
        _check_coverage(SuggestionItem, suggestions[0], "SuggestionItem")


def test_dataset_meta_fields(client: httpx.Client) -> None:
    resp = client.get("/datasets/fred/unemployment-rate/meta")
    resp.raise_for_status()
    data = resp.json()

    _check_coverage(DatasetMeta, data, "GET /datasets/.../meta")

    schema_info = data.get("schema_info", {})
    columns = schema_info.get("columns", [])
    if columns:
        _check_coverage(ColumnStats, columns[0], "ColumnStats in schema_info")


def test_data_page_fields(client: httpx.Client) -> None:
    resp = client.get(
        "/datasets/fred/unemployment-rate",
        params={"response_format": "columnar", "limit": "1"},
    )
    resp.raise_for_status()
    data = resp.json()

    _check_coverage(DataPage, data, "GET /datasets/... (columnar)")


def test_provider_fields(client: httpx.Client) -> None:
    resp = client.get("/providers")
    resp.raise_for_status()
    data = resp.json()
    items = data.get("items", [])
    if not items:
        pytest.skip("No providers returned")

    _check_coverage(Provider, items[0], "GET /providers")


def test_category_fields(client: httpx.Client) -> None:
    resp = client.get("/categories")
    resp.raise_for_status()
    data = resp.json()
    categories = data.get("categories", [])
    if not categories:
        pytest.skip("No categories returned")

    _check_coverage(Category, categories[0], "GET /categories")
