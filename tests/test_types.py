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
    SqlPage,
    SuggestionItem,
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
    assert m.description_layman is None
    assert m.temporal_coverage_start is None
    assert m.temporal_coverage_end is None
    assert m.graph is None


def test_dataset_meta_enrichment_fields():
    m = DatasetMeta.model_validate(
        {
            "id": "abc",
            "name": "Test",
            "path": "test/test",
            "status": "ready",
            "created_at": NOW,
            "updated_at": NOW,
            "description_layman": "A simple description",
            "temporal_coverage_start": "2020-01-01T00:00:00Z",
            "temporal_coverage_end": "2025-12-31T00:00:00Z",
            "graph": {"importance": 0.8, "bridge_score": 0.3},
        }
    )
    assert m.description_layman == "A simple description"
    assert m.temporal_coverage_start is not None
    assert m.temporal_coverage_end is not None
    assert m.graph == {"importance": 0.8, "bridge_score": 0.3}


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


def test_data_page_parses_api_format():
    """API returns 'types' and 'rows' (not 'column_types' and 'data')."""
    page = DataPage.model_validate(
        {
            "columns": ["year", "value"],
            "types": ["INTEGER", "DOUBLE"],
            "rows": [[2020, 1.5], [2021, 2.3]],
            "total_rows": 100,
        }
    )
    assert page.columns == ["year", "value"]
    assert page.column_types == ["INTEGER", "DOUBLE"]
    assert len(page.data) == 2
    assert page.data == [[2020, 1.5], [2021, 2.3]]
    assert page.total_rows == 100


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
    assert sr.is_starred is None
    assert sr.match_type is None
    assert sr.semantic_score is None
    assert sr.quality_score is None
    assert sr.importance is None


def test_search_result_enrichment_fields():
    sr = SearchResult.model_validate(
        {
            "id": "abc",
            "name": "CPI",
            "slug": "cpi-u",
            "path": "bls/cpi-u",
            "match_type": "both",
            "semantic_score": 0.85,
            "quality_score": 0.9,
            "importance": 0.7,
            "bridge_score": 0.3,
            "community_id": 5,
            "community_label": "Economic Indicators",
            "is_starred": True,
            "query_count": 42,
            "download_count": 100,
        }
    )
    assert sr.match_type == "both"
    assert sr.semantic_score == 0.85
    assert sr.quality_score == 0.9
    assert sr.importance == 0.7
    assert sr.bridge_score == 0.3
    assert sr.community_id == 5
    assert sr.community_label == "Economic Indicators"
    assert sr.is_starred is True
    assert sr.query_count == 42
    assert sr.download_count == 100


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
    assert resp.suggestions is None
    assert resp.processing_time_ms is None


def test_suggest_response():
    resp = SuggestResponse.model_validate(
        {
            "suggestions": [
                {
                    "id": "abc",
                    "name": "Inflation Rate",
                    "slug": "inflation",
                    "provider": "fred",
                    "path": "fred/inflation",
                }
            ],
            "query": "inf",
        }
    )
    assert len(resp.suggestions) == 1
    assert resp.suggestions[0].name == "Inflation Rate"
    assert resp.suggestions[0].provider == "fred"
    assert resp.query == "inf"
    assert resp.did_you_mean is None


def test_suggest_response_did_you_mean():
    resp = SuggestResponse.model_validate(
        {
            "suggestions": [],
            "query": "inflaton",
            "did_you_mean": "inflation",
        }
    )
    assert resp.did_you_mean == "inflation"
    assert resp.suggestions == []


def test_suggestion_item():
    item = SuggestionItem.model_validate(
        {
            "id": "abc",
            "name": "CPI",
            "slug": "cpi-u",
            "provider": "bls",
            "path": "bls/cpi-u",
            "description": "Consumer Price Index",
        }
    )
    assert item.name == "CPI"
    assert item.provider == "bls"
    assert item.description == "Consumer Price Index"


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
    assert p.base_url is None


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
            "supported_aggregations": ["sum", "avg", "min", "max"],
        }
    )
    assert cs.name == "year"
    assert cs.min == 1970
    assert cs.sample_values == [2020, 2021, 2022]
    assert cs.supported_aggregations == ["sum", "avg", "min", "max"]


def test_column_stats_defaults():
    cs = ColumnStats.model_validate({"name": "x", "type": "string"})
    assert cs.raw_type is None
    assert cs.distinct_count is None
    assert cs.sample_values is None
    assert cs.supported_aggregations is None


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


# -- SqlPage ---------------------------------------------------------------


def test_sql_page_parses():
    page = SqlPage.model_validate(
        {
            "columns": ["year", "value"],
            "types": ["INTEGER", "DOUBLE"],
            "rows": [[2020, 1.5], [2021, 2.3]],
            "row_count": 2,
            "execution_time_ms": 125.0,
            "truncated": False,
        }
    )
    assert page.columns == ["year", "value"]
    assert page.types == ["INTEGER", "DOUBLE"]
    assert len(page.rows) == 2
    assert page.row_count == 2
    assert page.execution_time_ms == 125.0
    assert page.truncated is False


def test_sql_page_extra_ignored():
    page = SqlPage.model_validate(
        {
            "columns": ["a"],
            "types": ["INTEGER"],
            "rows": [[1]],
            "row_count": 1,
            "some_future_field": "whatever",
        }
    )
    assert page.columns == ["a"]
    assert not hasattr(page, "some_future_field")


def test_sql_page_to_data_page():
    page = SqlPage.model_validate(
        {
            "columns": ["year", "value"],
            "types": ["INTEGER", "DOUBLE"],
            "rows": [[2020, 1.5], [2021, 2.3]],
            "row_count": 2,
        }
    )
    dp = page.to_data_page()
    assert isinstance(dp, DataPage)
    assert dp.columns == ["year", "value"]
    assert dp.column_types == ["INTEGER", "DOUBLE"]
    assert dp.data == [[2020, 1.5], [2021, 2.3]]
    assert dp.total_rows == 2


def test_sql_page_defaults():
    page = SqlPage.model_validate({})
    assert page.columns == []
    assert page.types == []
    assert page.rows == []
    assert page.row_count == 0
    assert page.execution_time_ms == 0.0
    assert page.truncated is False
    assert page.warnings is None
