from __future__ import annotations

import json

import httpx
import respx

from opendata_sdk._result import SqlResult
from opendata_sdk.aio import OpenData

from .conftest import BASE_URL, make_sql_page

BASE = BASE_URL


@respx.mock
async def test_single_dataset_routing():
    route = respx.post(f"{BASE}/datasets/fred/gdp/query").mock(
        return_value=httpx.Response(200, json=make_sql_page())
    )
    async with OpenData() as client:
        result = await client.sql.execute("SELECT * FROM fred/gdp")
        assert isinstance(result, SqlResult)
        assert route.called


@respx.mock
async def test_cross_dataset_routing():
    route = respx.post(f"{BASE}/query").mock(return_value=httpx.Response(200, json=make_sql_page()))
    async with OpenData() as client:
        await client.sql.execute(
            "SELECT a.year, b.pop FROM fred/gdp a JOIN census/pop b ON a.year = b.year"
        )
        assert route.called


@respx.mock
async def test_response_parsing():
    respx.post(f"{BASE}/datasets/fred/gdp/query").mock(
        return_value=httpx.Response(
            200,
            json=make_sql_page(
                columns=["year", "value"],
                types=["INTEGER", "DOUBLE"],
                rows=[[2020, 1.5], [2021, 2.3]],
                row_count=2,
                execution_time_ms=200.0,
                truncated=False,
            ),
        )
    )
    async with OpenData() as client:
        result = await client.sql.execute("SELECT * FROM fred/gdp")
        assert result.columns == ["year", "value"]
        assert len(result.rows) == 2
        assert result.rows[0] == {"year": 2020, "value": 1.5}
        assert result.execution_time_ms == 200.0
        assert result.truncated is False
        assert result.row_count == 2


@respx.mock
async def test_explicit_dataset_param():
    route = respx.post(f"{BASE}/datasets/fred/gdp/query").mock(
        return_value=httpx.Response(200, json=make_sql_page())
    )
    async with OpenData() as client:
        await client.sql.execute("SELECT * FROM t", dataset="fred/gdp")
        assert route.called


@respx.mock
async def test_request_body_correctness():
    route = respx.post(f"{BASE}/datasets/fred/gdp/query").mock(
        return_value=httpx.Response(200, json=make_sql_page())
    )
    async with OpenData() as client:
        await client.sql.execute(
            "SELECT * FROM fred/gdp",
            params=[2020],
            timeout_ms=5000,
            row_limit=500,
        )
        body = json.loads(route.calls.last.request.content)
        assert body["sql"] == 'SELECT * FROM "fred/gdp"'
        assert body["response_format"] == "columnar"
        assert body["params"] == [2020]
        assert body["timeout_ms"] == 5000
        assert body["row_limit"] == 500


@respx.mock
async def test_warnings_come_through():
    respx.post(f"{BASE}/datasets/fred/gdp/query").mock(
        return_value=httpx.Response(
            200,
            json=make_sql_page(
                warnings=["Slow query"],
            ),
        )
    )
    async with OpenData() as client:
        result = await client.sql.execute("SELECT * FROM fred/gdp")
        assert result.sql_warnings == ["Slow query"]


@respx.mock
async def test_zero_ref_routing():
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
    async with OpenData() as client:
        await client.sql.execute("SELECT 1+1")
        assert route.called
