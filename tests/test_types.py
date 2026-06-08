from __future__ import annotations

from opendata_sdk._types import (
    Category,
    ColumnStats,
    DataPage,
    Dataset,
    DatasetMeta,
    Provider,
    SearchResponse,
    SearchResult,
    SuggestResponse,
    ViewInfo,
)

NOW = "2026-01-15T12:00:00Z"


def test_dataset_parses():
    d = Dataset.model_validate(
        {
            "id": "abc",
            "name": "Test",
            "path": "test/test",
            "status": "ready",
            "created_at": NOW,
            "updated_at": NOW,
        }
    )
    assert d.id == "abc"
    assert d.name == "Test"
    assert d.status == "ready"


def test_dataset_optional_defaults():
    d = Dataset.model_validate(
        {
            "id": "abc",
            "name": "Test",
            "path": "test/test",
            "status": "ready",
            "created_at": NOW,
            "updated_at": NOW,
        }
    )
    assert d.slug is None
    assert d.description is None
    assert d.rows is None
    assert d.star_count is None
    assert d.provider is None


def test_dataset_extra_fields_ignored():
    d = Dataset.model_validate(
        {
            "id": "abc",
            "name": "Test",
            "path": "test/test",
            "status": "ready",
            "created_at": NOW,
            "updated_at": NOW,
            "some_future_field": "whatever",
            "another_new_thing": 42,
        }
    )
    assert d.id == "abc"
    assert not hasattr(d, "some_future_field")


def test_dataset_meta_parses():
    m = DatasetMeta.model_validate(
        {
            "id": "abc",
            "name": "Test",
            "path": "test/test",
            "status": "ready",
            "source_url": "https://example.com/data.csv",
            "schema_info": {"columns": []},
            "available_views": [{"name": "default"}],
            "created_at": NOW,
            "updated_at": NOW,
        }
    )
    assert m.source_url == "https://example.com/data.csv"
    assert m.available_views is not None
    assert len(m.available_views) == 1
    assert m.available_views[0].name == "default"


def test_dataset_meta_optional_defaults():
    m = DatasetMeta.model_validate(
        {
            "id": "abc",
            "name": "Test",
            "path": "test/test",
            "status": "ready",
            "created_at": NOW,
            "updated_at": NOW,
        }
    )
    assert m.source_url is None
    assert m.schema_info is None
    assert m.available_views is None
    assert m.default_view is None
    assert m.semantic_entity is None
    assert m.parquet_size_bytes is None


def test_data_page_parses():
    page = DataPage.model_validate(
        {
            "columns": ["year", "value"],
            "column_types": ["INTEGER", "DOUBLE"],
            "data": [[2020, 1.5], [2021, 2.3]],
            "total_rows": 100,
        }
    )
    assert page.columns == ["year", "value"]
    assert len(page.data) == 2
    assert page.total_rows == 100


def test_data_page_defaults():
    page = DataPage.model_validate({})
    assert page.columns == []
    assert page.column_types == []
    assert page.data == []
    assert page.total_rows is None
    assert page.next_cursor is None
    assert page.warnings == []


def test_data_page_extra_ignored():
    page = DataPage.model_validate(
        {
            "columns": ["a"],
            "data": [[1]],
            "new_api_field": True,
        }
    )
    assert page.columns == ["a"]


def test_search_result_parses():
    sr = SearchResult.model_validate(
        {
            "id": "abc",
            "name": "CPI",
            "slug": "cpi-u",
            "path": "bls/cpi-u",
            "relevance": 0.95,
        }
    )
    assert sr.relevance == 0.95
    assert sr.slug == "cpi-u"


def test_search_result_defaults():
    sr = SearchResult.model_validate(
        {
            "id": "abc",
            "name": "CPI",
            "slug": "cpi-u",
            "path": "bls/cpi-u",
        }
    )
    assert sr.description is None
    assert sr.rows is None
    assert sr.highlights is None
    assert sr.categories == []
    assert sr.star_count is None


def test_search_response_parses():
    resp = SearchResponse.model_validate(
        {
            "results": [
                {"id": "1", "name": "A", "slug": "a", "path": "x/a"},
                {"id": "2", "name": "B", "slug": "b", "path": "x/b"},
            ],
            "total": 2,
            "limit": 20,
            "offset": 0,
            "query": "test",
        }
    )
    assert len(resp.results) == 2
    assert resp.total == 2
    assert resp.query == "test"


def test_search_response_defaults():
    resp = SearchResponse.model_validate({})
    assert resp.results == []
    assert resp.total == 0
    assert resp.limit == 20
    assert resp.offset == 0
    assert resp.facets is None
    assert resp.processing_time_ms is None


def test_suggest_response():
    resp = SuggestResponse.model_validate(
        {
            "suggestions": [{"text": "inflation", "score": 0.9}],
            "query": "inf",
        }
    )
    assert len(resp.suggestions) == 1
    assert resp.query == "inf"


def test_provider_parses():
    p = Provider.model_validate(
        {
            "id": "abc",
            "slug": "bls",
            "name": "Bureau of Labor Statistics",
        }
    )
    assert p.slug == "bls"
    assert p.description is None
    assert p.dataset_count is None


def test_category_parses():
    c = Category.model_validate(
        {
            "slug": "economics",
            "name": "Economics",
            "dataset_count": 15,
        }
    )
    assert c.slug == "economics"
    assert c.dataset_count == 15
    assert c.icon is None


def test_column_stats_parses():
    cs = ColumnStats.model_validate(
        {
            "name": "year",
            "type": "integer",
            "raw_type": "INTEGER",
            "distinct_count": 50,
            "null_count": 0,
            "min": 1970,
            "max": 2024,
            "sample_values": [2020, 2021, 2022],
        }
    )
    assert cs.name == "year"
    assert cs.min == 1970
    assert cs.sample_values == [2020, 2021, 2022]


def test_column_stats_defaults():
    cs = ColumnStats.model_validate({"name": "x", "type": "string"})
    assert cs.raw_type is None
    assert cs.distinct_count is None
    assert cs.sample_values is None


def test_view_info_parses():
    v = ViewInfo.model_validate(
        {
            "name": "timeseries",
            "description": "Time series view",
            "capabilities": ["sort", "filter"],
        }
    )
    assert v.name == "timeseries"
    assert v.capabilities == ["sort", "filter"]


def test_view_info_defaults():
    v = ViewInfo.model_validate({"name": "default"})
    assert v.description is None
    assert v.capabilities == []
    assert v.example_url is None
