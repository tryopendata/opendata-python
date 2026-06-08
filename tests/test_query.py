from __future__ import annotations

import logging

from opendata_sdk._query import Query


def test_empty_query_produces_empty_params():
    q = Query()
    assert q._to_params() == {}


def test_fields():
    params = Query().fields("a", "b")._to_params()
    assert params == {"fields": "a,b"}


def test_eq_filter():
    params = Query().eq("state", "CA")._to_params()
    assert params == {"filter[state]": "CA"}


def test_gte_filter():
    params = Query().gte("year", 2020)._to_params()
    assert params == {"filter[year][gte]": "2020"}


def test_ne_filter():
    params = Query().ne("status", "error")._to_params()
    assert params == {"filter[status][ne]": "error"}


def test_gt_filter():
    params = Query().gt("value", 100)._to_params()
    assert params == {"filter[value][gt]": "100"}


def test_lt_filter():
    params = Query().lt("value", 50)._to_params()
    assert params == {"filter[value][lt]": "50"}


def test_lte_filter():
    params = Query().lte("year", 2025)._to_params()
    assert params == {"filter[year][lte]": "2025"}


def test_like_filter():
    params = Query().like("name", "%test%")._to_params()
    assert params == {"filter[name][like]": "%test%"}


def test_isin_filter():
    params = Query().isin("state", ["CA", "TX"])._to_params()
    assert params == {"filter[state][in]": "CA,TX"}


def test_isin_with_ints():
    params = Query().isin("year", [2020, 2021, 2022])._to_params()
    assert params == {"filter[year][in]": "2020,2021,2022"}


def test_sort_ascending():
    params = Query().sort("date")._to_params()
    assert params == {"sort": "date"}


def test_sort_descending():
    params = Query().sort("date", desc=True)._to_params()
    assert params == {"sort": "-date"}


def test_multiple_sorts():
    params = Query().sort("year").sort("value", desc=True)._to_params()
    assert params == {"sort": "year,-value"}


def test_limit_and_offset():
    params = Query().limit(10).offset(20)._to_params()
    assert params == {"limit": "10", "offset": "20"}


def test_view():
    params = Query().view("timeseries")._to_params()
    assert params == {"view": "timeseries"}


def test_group_by_and_aggregate():
    params = Query().group_by("region").aggregate("sum:value")._to_params()
    assert params == {"group_by": "region", "aggregate": "sum:value"}


def test_multiple_aggregates():
    params = Query().group_by("region").aggregate("sum:value", "count:id")._to_params()
    assert params == {"group_by": "region", "aggregate": "sum:value,count:id"}


def test_chaining_produces_combined_params():
    params = (
        Query()
        .fields("year", "value")
        .eq("state", "CA")
        .gte("year", 2020)
        .sort("year", desc=True)
        .limit(50)
        .view("timeseries")
        ._to_params()
    )
    assert params == {
        "fields": "year,value",
        "filter[state]": "CA",
        "filter[year][gte]": "2020",
        "sort": "-year",
        "limit": "50",
        "view": "timeseries",
    }


def test_immutability():
    """Modifying a derived query should not affect the original."""
    original = Query().eq("state", "CA")
    derived = original.gte("year", 2020)

    original_params = original._to_params()
    derived_params = derived._to_params()

    assert "filter[year][gte]" not in original_params
    assert "filter[year][gte]" in derived_params
    assert original_params == {"filter[state]": "CA"}


def test_immutability_fields():
    """Fields list should not be shared between copies."""
    original = Query().fields("a")
    derived = original.fields("b", "c")

    assert original._to_params() == {"fields": "a"}
    assert derived._to_params() == {"fields": "b,c"}


def test_mixed_case_column_warns(caplog):
    with caplog.at_level(logging.WARNING, logger="opendata_sdk"):
        Query().eq("MyColumn", "val")
    assert "MyColumn" in caplog.text
    assert "uppercase" in caplog.text


def test_valid_column_no_warning(caplog):
    with caplog.at_level(logging.WARNING, logger="opendata_sdk"):
        Query().eq("my_column", "val")
    assert caplog.text == ""


def test_repr_empty():
    assert "empty" in repr(Query())


def test_repr_with_parts():
    q = Query().fields("a").limit(10).view("ts")
    r = repr(q)
    assert "fields" in r
    assert "limit" in r
    assert "view" in r


def test_filter_with_explicit_operator():
    params = Query().filter("value", "gte", 100)._to_params()
    assert params == {"filter[value][gte]": "100"}
