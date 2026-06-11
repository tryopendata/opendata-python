from __future__ import annotations

import json

import httpx
import pytest
import respx

from opendata_sdk import OpenData
from opendata_sdk._result import SqlResult

from .conftest import BASE_URL, make_sql_page

BASE = BASE_URL


# -- Routing ---------------------------------------------------------------


@respx.mock
def test_single_dataset_routes_to_dataset_endpoint():
    route = respx.post(f"{BASE}/datasets/fred/gdp/query").mock(
        return_value=httpx.Response(200, json=make_sql_page())
    )
    client = OpenData()
    client.sql.execute("SELECT * FROM fred/gdp")
    assert route.called
    client.close()


@respx.mock
def test_cross_dataset_routes_to_query_endpoint():
    route = respx.post(f"{BASE}/query").mock(return_value=httpx.Response(200, json=make_sql_page()))
    client = OpenData()
    client.sql.execute("SELECT a.year, b.pop FROM fred/gdp a JOIN census/pop b ON a.year = b.year")
    assert route.called
    client.close()


@respx.mock
def test_zero_ref_routes_to_query_endpoint():
    route = respx.post(f"{BASE}/query").mock(
        return_value=httpx.Response(
            200,
            json=make_sql_page(
                columns=["result"],
                types=["INTEGER"],
                rows=[[2]],
                row_count=1,
            ),
        )
    )
    client = OpenData()
    client.sql.execute("SELECT 1+1")
    assert route.called
    client.close()


@respx.mock
def test_explicit_dataset_param_routes_to_dataset_endpoint():
    route = respx.post(f"{BASE}/datasets/fred/gdp/query").mock(
        return_value=httpx.Response(200, json=make_sql_page())
    )
    client = OpenData()
    client.sql.execute("SELECT * FROM t", dataset="fred/gdp")
    assert route.called
    client.close()


@respx.mock
def test_explicit_dataset_with_leading_slash():
    route = respx.post(f"{BASE}/datasets/fred/gdp/query").mock(
        return_value=httpx.Response(200, json=make_sql_page())
    )
    client = OpenData()
    client.sql.execute("SELECT * FROM t", dataset="/fred/gdp/")
    assert route.called
    client.close()


# -- Request body ----------------------------------------------------------


@respx.mock
def test_request_body_contains_sql_and_format():
    route = respx.post(f"{BASE}/datasets/fred/gdp/query").mock(
        return_value=httpx.Response(200, json=make_sql_page())
    )
    client = OpenData()
    client.sql.execute("SELECT * FROM fred/gdp")
    body = json.loads(route.calls.last.request.content)
    assert body["sql"] == 'SELECT * FROM "fred/gdp"'
    assert body["response_format"] == "columnar"
    client.close()


@respx.mock
def test_request_body_optional_fields():
    route = respx.post(f"{BASE}/datasets/fred/gdp/query").mock(
        return_value=httpx.Response(200, json=make_sql_page())
    )
    client = OpenData()
    client.sql.execute(
        "SELECT * FROM fred/gdp",
        params=[2020, "CA"],
        timeout_ms=5000,
        row_limit=100,
        view="enriched",
    )
    body = json.loads(route.calls.last.request.content)
    assert body["params"] == [2020, "CA"]
    assert body["timeout_ms"] == 5000
    assert body["row_limit"] == 100
    assert body["view"] == "enriched"
    client.close()


@respx.mock
def test_normalized_sql_in_body():
    """Bare slash refs should be quoted in the request body."""
    route = respx.post(f"{BASE}/datasets/fred/gdp/query").mock(
        return_value=httpx.Response(200, json=make_sql_page())
    )
    client = OpenData()
    client.sql.execute("SELECT * FROM fred/gdp")
    body = json.loads(route.calls.last.request.content)
    assert body["sql"] == 'SELECT * FROM "fred/gdp"'
    client.close()


@respx.mock
def test_dot_form_normalized_in_body():
    route = respx.post(f"{BASE}/datasets/fred/gdp/query").mock(
        return_value=httpx.Response(200, json=make_sql_page())
    )
    client = OpenData()
    client.sql.execute("SELECT * FROM fred.gdp")
    body = json.loads(route.calls.last.request.content)
    assert body["sql"] == 'SELECT * FROM "fred/gdp"'
    client.close()


@respx.mock
def test_params_binding_in_body():
    route = respx.post(f"{BASE}/datasets/fred/gdp/query").mock(
        return_value=httpx.Response(200, json=make_sql_page())
    )
    client = OpenData()
    client.sql.execute("SELECT * FROM fred/gdp WHERE year = ?", params=[2020])
    body = json.loads(route.calls.last.request.content)
    assert body["params"] == [2020]
    client.close()


# -- Response parsing ------------------------------------------------------


@respx.mock
def test_response_returns_sql_result():
    respx.post(f"{BASE}/datasets/fred/gdp/query").mock(
        return_value=httpx.Response(200, json=make_sql_page())
    )
    client = OpenData()
    result = client.sql.execute("SELECT * FROM fred/gdp")
    assert isinstance(result, SqlResult)
    client.close()


@respx.mock
def test_response_rows_and_columns():
    respx.post(f"{BASE}/datasets/fred/gdp/query").mock(
        return_value=httpx.Response(
            200,
            json=make_sql_page(
                columns=["year", "value"],
                types=["INTEGER", "DOUBLE"],
                rows=[[2020, 1.5], [2021, 2.3]],
                row_count=2,
            ),
        )
    )
    client = OpenData()
    result = client.sql.execute("SELECT * FROM fred/gdp")
    assert result.columns == ["year", "value"]
    assert len(result.rows) == 2
    assert result.rows[0] == {"year": 2020, "value": 1.5}
    assert result.rows[1] == {"year": 2021, "value": 2.3}
    client.close()


@respx.mock
def test_response_metadata():
    respx.post(f"{BASE}/datasets/fred/gdp/query").mock(
        return_value=httpx.Response(
            200,
            json=make_sql_page(
                execution_time_ms=250.5,
                truncated=True,
                row_count=10000,
            ),
        )
    )
    client = OpenData()
    result = client.sql.execute("SELECT * FROM fred/gdp")
    assert result.execution_time_ms == 250.5
    assert result.truncated is True
    assert result.row_count == 10000
    client.close()


@respx.mock
def test_response_warnings():
    respx.post(f"{BASE}/datasets/fred/gdp/query").mock(
        return_value=httpx.Response(
            200,
            json=make_sql_page(
                warnings=["Results truncated to 10000 rows"],
            ),
        )
    )
    client = OpenData()
    result = client.sql.execute("SELECT * FROM fred/gdp")
    assert result.sql_warnings == ["Results truncated to 10000 rows"]
    client.close()


@respx.mock
def test_response_warnings_default_empty():
    respx.post(f"{BASE}/datasets/fred/gdp/query").mock(
        return_value=httpx.Response(200, json=make_sql_page(warnings=None))
    )
    client = OpenData()
    result = client.sql.execute("SELECT * FROM fred/gdp")
    assert result.sql_warnings == []
    client.close()


# -- DataFrame conversions -------------------------------------------------


@respx.mock
def test_to_pandas():
    respx.post(f"{BASE}/datasets/fred/gdp/query").mock(
        return_value=httpx.Response(200, json=make_sql_page())
    )
    client = OpenData()
    result = client.sql.execute("SELECT * FROM fred/gdp")
    df = result.to_pandas()
    assert list(df.columns) == ["year", "value"]
    assert len(df) == 2
    client.close()


@respx.mock
def test_to_polars():
    import polars as pl

    respx.post(f"{BASE}/datasets/fred/gdp/query").mock(
        return_value=httpx.Response(200, json=make_sql_page())
    )
    client = OpenData()
    result = client.sql.execute("SELECT * FROM fred/gdp")
    df = result.to_polars()
    assert isinstance(df, pl.DataFrame)
    assert df.columns == ["year", "value"]
    assert len(df) == 2
    client.close()


# -- repr ------------------------------------------------------------------


@respx.mock
def test_sql_result_repr():
    respx.post(f"{BASE}/datasets/fred/gdp/query").mock(
        return_value=httpx.Response(
            200,
            json=make_sql_page(
                execution_time_ms=125.0,
            ),
        )
    )
    client = OpenData()
    result = client.sql.execute("SELECT * FROM fred/gdp")
    r = repr(result)
    assert "SqlResult" in r
    assert "rows=2" in r
    assert "columns=2" in r
    assert "time=125ms" in r
    client.close()


# -- Validation errors -----------------------------------------------------


def test_empty_sql_raises():
    client = OpenData()
    with pytest.raises(ValueError, match="non-empty string"):
        client.sql.execute("")
    client.close()


def test_whitespace_only_sql_raises():
    client = OpenData()
    with pytest.raises(ValueError, match="non-empty string"):
        client.sql.execute("   ")
    client.close()


def test_sql_too_long_raises():
    client = OpenData()
    with pytest.raises(ValueError, match="100,000 characters"):
        client.sql.execute("x" * 100_001)
    client.close()


def test_timeout_ms_too_low_raises():
    client = OpenData()
    with pytest.raises(ValueError, match="timeout_ms must be between"):
        client.sql.execute("SELECT 1", timeout_ms=99)
    client.close()


def test_timeout_ms_zero_raises():
    client = OpenData()
    with pytest.raises(ValueError, match="timeout_ms must be between"):
        client.sql.execute("SELECT 1", timeout_ms=0)
    client.close()


def test_timeout_ms_too_high_raises():
    client = OpenData()
    with pytest.raises(ValueError, match="timeout_ms must be between"):
        client.sql.execute("SELECT 1", timeout_ms=10001)
    client.close()


def test_row_limit_zero_raises():
    client = OpenData()
    with pytest.raises(ValueError, match="row_limit must be between"):
        client.sql.execute("SELECT 1", row_limit=0)
    client.close()


def test_row_limit_too_high_raises():
    client = OpenData()
    with pytest.raises(ValueError, match="row_limit must be between"):
        client.sql.execute("SELECT 1", row_limit=10001)
    client.close()


def test_invalid_dataset_path_raises():
    client = OpenData()
    with pytest.raises(ValueError, match="provider/dataset"):
        client.sql.execute("SELECT 1", dataset="just-one-part")
    client.close()


def test_invalid_dataset_path_three_parts_raises():
    client = OpenData()
    with pytest.raises(ValueError, match="provider/dataset"):
        client.sql.execute("SELECT 1", dataset="a/b/c")
    client.close()
