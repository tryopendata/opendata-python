from __future__ import annotations

import httpx
import pytest
import respx

from opendata_sdk import OpenData, Query
from opendata_sdk._pagination import PaginatedList
from opendata_sdk._result import DataResult
from opendata_sdk._types import ColumnStats, DatasetMeta, ViewInfo

from .conftest import make_data_page, make_dataset, make_dataset_list, make_dataset_meta

BASE = "https://api.tryopendata.ai/v1"


@respx.mock
def test_list_makes_get_datasets():
    route = respx.get(f"{BASE}/datasets").mock(
        return_value=httpx.Response(200, json=make_dataset_list())
    )
    client = OpenData()
    result = client.datasets.list()
    assert isinstance(result, PaginatedList)
    assert len(result) == 1
    items = list(result)
    assert items[0].name == "CPI-U"
    assert route.called
    client.close()


@respx.mock
def test_list_with_provider():
    route = respx.get(f"{BASE}/datasets/bls").mock(
        return_value=httpx.Response(200, json=make_dataset_list())
    )
    client = OpenData()
    client.datasets.list(provider="bls")
    assert route.called
    client.close()


@respx.mock
def test_list_with_status_and_sort():
    route = respx.get(f"{BASE}/datasets").mock(
        return_value=httpx.Response(200, json=make_dataset_list())
    )
    client = OpenData()
    client.datasets.list(status="ready", sort="-updated_at")
    req = route.calls.last.request
    assert "status=ready" in str(req.url)
    assert "sort=-updated_at" in str(req.url)
    client.close()


@respx.mock
def test_get_makes_get_meta():
    meta = make_dataset_meta()
    route = respx.get(f"{BASE}/datasets/bls/cpi-u/meta").mock(
        return_value=httpx.Response(200, json=meta)
    )
    client = OpenData()
    result = client.datasets.get("bls/cpi-u")
    assert isinstance(result, DatasetMeta)
    assert result.name == "CPI-U"
    assert route.called
    client.close()


@respx.mock
def test_query_makes_get_with_columnar():
    route = respx.get(f"{BASE}/datasets/bls/cpi-u").mock(
        return_value=httpx.Response(200, json=make_data_page())
    )
    client = OpenData()
    result = client.datasets.query("bls/cpi-u")
    assert isinstance(result, DataResult)
    assert "response_format=columnar" in str(route.calls.last.request.url)
    client.close()


@respx.mock
def test_query_with_query_builder():
    route = respx.get(f"{BASE}/datasets/bls/cpi-u").mock(
        return_value=httpx.Response(200, json=make_data_page())
    )
    client = OpenData()
    q = Query().gte("year", 2020).eq("state", "CA")
    client.datasets.query("bls/cpi-u", query=q)
    url = str(route.calls.last.request.url)
    assert "filter%5Byear%5D%5Bgte%5D=2020" in url or "filter[year][gte]=2020" in url
    client.close()


@respx.mock
def test_query_all_merges_pages():
    page1 = make_data_page(
        rows=[[2020, 1.5], [2021, 2.3]],
        next_cursor="cur1",
        total_rows=4,
    )
    page2 = make_data_page(
        rows=[[2022, 3.1], [2023, 4.0]],
        next_cursor=None,
        total_rows=4,
    )
    respx.get(f"{BASE}/datasets/bls/cpi-u").mock(
        side_effect=[
            httpx.Response(200, json=page1),
            httpx.Response(200, json=page2),
        ]
    )
    client = OpenData()
    result = client.datasets.query_all("bls/cpi-u")
    assert len(result) == 4
    assert result.rows[0]["year"] == 2020
    assert result.rows[3]["year"] == 2023
    client.close()


@respx.mock
def test_query_iter_yields_pages():
    page1 = make_data_page(rows=[[2020, 1.5]], next_cursor="cur1")
    page2 = make_data_page(rows=[[2021, 2.3]], next_cursor=None)
    respx.get(f"{BASE}/datasets/bls/cpi-u").mock(
        side_effect=[
            httpx.Response(200, json=page1),
            httpx.Response(200, json=page2),
        ]
    )
    client = OpenData()
    pages = list(client.datasets.query_iter("bls/cpi-u"))
    assert len(pages) == 2
    assert len(pages[0]) == 1
    assert len(pages[1]) == 1
    client.close()


@respx.mock
def test_hierarchical_dataset_raises():
    respx.get(f"{BASE}/datasets/bls/employment").mock(
        return_value=httpx.Response(
            200,
            json={
                "subdatasets": [
                    {"slug": "national"},
                    {"slug": "state"},
                ],
            },
        )
    )
    client = OpenData()
    with pytest.raises(ValueError, match="hierarchical dataset"):
        client.datasets.query("bls/employment")
    client.close()


@respx.mock
def test_columns_returns_list():
    respx.get(f"{BASE}/datasets/bls/cpi-u/columns").mock(
        return_value=httpx.Response(
            200,
            json={
                "columns": [
                    {"name": "year", "type": "integer", "distinct_count": 50},
                    {"name": "value", "type": "float"},
                ]
            },
        )
    )
    client = OpenData()
    cols = client.datasets.columns("bls/cpi-u")
    assert len(cols) == 2
    assert all(isinstance(c, ColumnStats) for c in cols)
    assert cols[0].name == "year"
    client.close()


@respx.mock
def test_views_returns_list():
    respx.get(f"{BASE}/datasets/bls/cpi-u/views").mock(
        return_value=httpx.Response(
            200,
            json={
                "views": [
                    {"name": "default"},
                    {"name": "timeseries", "capabilities": ["sort"]},
                ]
            },
        )
    )
    client = OpenData()
    views = client.datasets.views("bls/cpi-u")
    assert len(views) == 2
    assert all(isinstance(v, ViewInfo) for v in views)
    assert views[1].name == "timeseries"
    client.close()


@respx.mock
def test_create_sends_post():
    meta = make_dataset_meta()
    route = respx.post(f"{BASE}/datasets").mock(return_value=httpx.Response(201, json=meta))
    client = OpenData()
    result = client.datasets.create({"source_url": "https://example.com/data.csv"})
    assert isinstance(result, DatasetMeta)
    assert route.called
    client.close()


@respx.mock
def test_delete_sends_delete():
    route = respx.delete(f"{BASE}/datasets/bls/cpi-u").mock(return_value=httpx.Response(204))
    client = OpenData()
    client.datasets.delete("bls/cpi-u")
    assert route.called
    client.close()


def test_invalid_path_raises():
    client = OpenData()
    with pytest.raises(ValueError, match="provider/dataset"):
        client.datasets.get("just-one-part")
    client.close()


def test_invalid_path_three_parts():
    client = OpenData()
    with pytest.raises(ValueError, match="provider/dataset"):
        client.datasets.get("a/b/c")
    client.close()


@respx.mock
def test_update_sends_patch():
    ds = make_dataset()
    route = respx.patch(f"{BASE}/datasets/bls/cpi-u").mock(
        return_value=httpx.Response(200, json=ds)
    )
    client = OpenData()
    result = client.datasets.update("bls/cpi-u", {"description": "Updated"})
    assert result.name == "CPI-U"
    assert route.called
    client.close()


@respx.mock
def test_sync_sends_post():
    route = respx.post(f"{BASE}/datasets/bls/cpi-u/sync").mock(return_value=httpx.Response(202))
    client = OpenData()
    client.datasets.sync("bls/cpi-u")
    assert route.called
    client.close()


@respx.mock
def test_related_returns_datasets():
    ds = make_dataset(id="xyz", name="PPI", path="bls/ppi")
    respx.get(f"{BASE}/datasets/bls/cpi-u/related").mock(
        return_value=httpx.Response(
            200,
            json={"related_datasets": [ds]},
        )
    )
    client = OpenData()
    related = client.datasets.related("bls/cpi-u")
    assert len(related) == 1
    assert related[0].name == "PPI"
    client.close()


@respx.mock
def test_query_all_with_max_rows():
    page = make_data_page(
        rows=[[2020, 1.5], [2021, 2.3], [2022, 3.1]],
        next_cursor=None,
        total_rows=3,
    )
    respx.get(f"{BASE}/datasets/bls/cpi-u").mock(return_value=httpx.Response(200, json=page))
    client = OpenData()
    result = client.datasets.query_all("bls/cpi-u", max_rows=2)
    assert len(result) == 2
    client.close()


@respx.mock
def test_columns_with_view():
    route = respx.get(f"{BASE}/datasets/bls/cpi-u/columns").mock(
        return_value=httpx.Response(200, json={"columns": []})
    )
    client = OpenData()
    client.datasets.columns("bls/cpi-u", view="timeseries")
    url = str(route.calls.last.request.url)
    assert "view=timeseries" in url
    client.close()
