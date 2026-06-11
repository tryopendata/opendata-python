from __future__ import annotations

import sys
from unittest.mock import patch

import pytest

from opendata_sdk._result import DataResult, SqlResult
from opendata_sdk._types import DataPage


def _page(**kwargs) -> DataPage:
    defaults = {
        "columns": ["year", "value", "name"],
        "column_types": ["INTEGER", "DOUBLE", "VARCHAR"],
        "data": [
            [2020, 1.5, "alpha"],
            [2021, 2.3, "beta"],
            [2022, None, "gamma"],
        ],
        "total_rows": 100,
        "next_cursor": "abc123",
    }
    defaults.update(kwargs)
    return DataPage(**defaults)


def test_columns():
    result = DataResult(_page())
    assert result.columns == ["year", "value", "name"]


def test_rows_transposes_to_dicts():
    result = DataResult(_page())
    rows = result.rows
    assert len(rows) == 3
    assert rows[0] == {"year": 2020, "value": 1.5, "name": "alpha"}
    assert rows[1] == {"year": 2021, "value": 2.3, "name": "beta"}
    assert rows[2] == {"year": 2022, "value": None, "name": "gamma"}


def test_total_rows():
    result = DataResult(_page(total_rows=500))
    assert result.total_rows == 500


def test_next_cursor():
    result = DataResult(_page(next_cursor="cursor-xyz"))
    assert result.next_cursor == "cursor-xyz"


def test_next_cursor_none():
    result = DataResult(_page(next_cursor=None))
    assert result.next_cursor is None


def test_len():
    result = DataResult(_page())
    assert len(result) == 3


def test_len_empty():
    result = DataResult(_page(data=[]))
    assert len(result) == 0


def test_repr():
    result = DataResult(_page())
    assert "rows=3" in repr(result)
    assert "columns=3" in repr(result)


# ── pandas conversion ────────────────────────────────────────────────


def test_to_pandas_columns_and_dtypes():
    result = DataResult(_page())
    df = result.to_pandas()
    assert list(df.columns) == ["year", "value", "name"]
    assert df["year"].dtype.name == "Int64"
    assert df["value"].dtype.name == "Float64"
    assert df["name"].dtype.name == "string"


def test_to_pandas_null_values():
    """Nullable Int64 should preserve None as pd.NA, not NaN."""
    import pandas as pd

    result = DataResult(_page())
    df = result.to_pandas()
    assert pd.isna(df["value"].iloc[2])


def test_to_pandas_date_coercion():
    page = DataPage(
        columns=["dt"],
        column_types=["TIMESTAMP"],
        data=[["2020-01-15T00:00:00"], ["2021-06-01T12:30:00"]],
        total_rows=2,
    )
    result = DataResult(page)
    df = result.to_pandas()
    assert "datetime64" in df["dt"].dtype.name


def test_to_pandas_date_type():
    page = DataPage(
        columns=["d"],
        column_types=["DATE"],
        data=[["2020-01-15"], ["2021-06-01"]],
        total_rows=2,
    )
    result = DataResult(page)
    df = result.to_pandas()
    assert "datetime" in df["d"].dtype.name


def test_to_pandas_boolean():
    page = DataPage(
        columns=["flag"],
        column_types=["BOOLEAN"],
        data=[[True], [False], [None]],
        total_rows=3,
    )
    result = DataResult(page)
    df = result.to_pandas()
    assert df["flag"].dtype.name == "boolean"


def test_to_pandas_empty():
    page = DataPage(columns=[], column_types=[], data=[], total_rows=0)
    result = DataResult(page)
    df = result.to_pandas()
    assert len(df) == 0
    assert list(df.columns) == []


def test_to_pandas_decimal_type():
    """DECIMAL(18,3) should strip precision and map to Float64."""
    page = DataPage(
        columns=["amount"],
        column_types=["DECIMAL(18,3)"],
        data=[[1.5], [2.7]],
        total_rows=2,
    )
    result = DataResult(page)
    df = result.to_pandas()
    assert df["amount"].dtype.name == "Float64"


def test_to_pandas_import_error():
    """Should raise ImportError with install instructions when pandas missing."""
    with patch.dict(sys.modules, {"pandas": None}):
        result = DataResult(_page())
        with pytest.raises(ImportError, match="opendata-sdk\\[pandas\\]"):
            result.to_pandas()


# ── polars conversion ────────────────────────────────────────────────


def test_to_polars_returns_dataframe():
    import polars as pl

    result = DataResult(_page())
    df = result.to_polars()
    assert isinstance(df, pl.DataFrame)
    assert df.columns == ["year", "value", "name"]
    assert len(df) == 3


def test_to_polars_column_oriented():
    """Data should be transposed from rows to columns."""
    result = DataResult(_page())
    df = result.to_polars()
    assert df["year"].to_list() == [2020, 2021, 2022]
    assert df["name"].to_list() == ["alpha", "beta", "gamma"]


def test_to_polars_empty():
    import polars as pl

    page = DataPage(columns=[], column_types=[], data=[], total_rows=0)
    result = DataResult(page)
    df = result.to_polars()
    assert isinstance(df, pl.DataFrame)
    assert len(df) == 0


def test_to_polars_import_error():
    with patch.dict(sys.modules, {"polars": None}):
        result = DataResult(_page())
        with pytest.raises(ImportError, match="opendata-sdk\\[polars\\]"):
            result.to_polars()


# ── Edge cases ───────────────────────────────────────────────────────


def test_rows_with_short_row():
    """Row shorter than columns list shouldn't crash."""
    page = DataPage(
        columns=["a", "b", "c"],
        column_types=["VARCHAR", "VARCHAR", "VARCHAR"],
        data=[["x", "y"]],  # missing third value
        total_rows=1,
    )
    result = DataResult(page)
    rows = result.rows
    # Only has keys for the values that exist
    assert rows[0] == {"a": "x", "b": "y"}


def test_column_types_shorter_than_columns():
    """If column_types has fewer entries than columns, no crash."""
    page = DataPage(
        columns=["a", "b"],
        column_types=["INTEGER"],  # only one type
        data=[[1, "x"], [2, "y"]],
        total_rows=2,
    )
    result = DataResult(page)
    df = result.to_pandas()
    assert df["a"].dtype.name == "Int64"
    assert len(df) == 2


# -- SqlResult -------------------------------------------------------------


def _sql_result(**kwargs) -> SqlResult:
    defaults = {
        "page": _page(),
        "execution_time_ms": 125.0,
        "truncated": False,
        "row_count": 3,
        "sql_warnings": [],
    }
    defaults.update(kwargs)
    page = defaults.pop("page")
    return SqlResult(page, **defaults)


def test_sql_result_inherits_data_result():
    result = _sql_result()
    assert isinstance(result, DataResult)
    assert result.columns == ["year", "value", "name"]
    assert len(result.rows) == 3
    assert result.rows[0] == {"year": 2020, "value": 1.5, "name": "alpha"}


def test_sql_result_metadata():
    result = _sql_result(execution_time_ms=250.5, truncated=True, row_count=10000)
    assert result.execution_time_ms == 250.5
    assert result.truncated is True
    assert result.row_count == 10000


def test_sql_result_sql_warnings():
    """SqlResult.sql_warnings returns list[str]."""
    result = _sql_result(sql_warnings=["Slow query", "Results truncated"])
    assert result.sql_warnings == ["Slow query", "Results truncated"]
    assert all(isinstance(w, str) for w in result.sql_warnings)


def test_sql_result_sql_warnings_empty():
    result = _sql_result(sql_warnings=[])
    assert result.sql_warnings == []


def test_sql_result_repr():
    result = _sql_result(execution_time_ms=125.0)
    r = repr(result)
    assert "SqlResult" in r
    assert "rows=3" in r
    assert "columns=3" in r
    assert "time=125ms" in r
