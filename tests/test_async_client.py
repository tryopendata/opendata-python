from __future__ import annotations

import os
from unittest.mock import patch

import httpx
import respx

from opendata_sdk._resources.datasets import AsyncDatasetResource
from opendata_sdk._resources.sql import AsyncSqlResource
from opendata_sdk._result import SqlResult
from opendata_sdk._types import SearchResponse, SuggestResponse
from opendata_sdk.aio import OpenData

from .conftest import (
    make_data_page,
    make_dataset_list,
    make_dataset_meta,
    make_search_response,
    make_sql_page,
    make_suggest_response,
)

BASE = "https://api.tryopendata.ai/v1"


async def test_constructor_with_api_key():
    client = OpenData(api_key="sk-async-test")
    assert client._transport._config.api_key == "sk-async-test"
    await client.close()


async def test_constructor_reads_env_var():
    with patch.dict(os.environ, {"OPENDATA_API_KEY": "sk-env-async"}):
        client = OpenData()
        assert client._transport._config.api_key == "sk-env-async"
        await client.close()


async def test_default_base_url():
    client = OpenData()
    assert client._transport._config.base_url == "https://api.tryopendata.ai/v1"
    await client.close()


async def test_datasets_property():
    client = OpenData()
    assert isinstance(client.datasets, AsyncDatasetResource)
    await client.close()


@respx.mock
async def test_async_context_manager():
    respx.get(f"{BASE}/search").mock(return_value=httpx.Response(200, json=make_search_response()))
    async with OpenData() as client:
        result = await client.search("test")
        assert isinstance(result, SearchResponse)
        assert result.total == 1


@respx.mock
async def test_search_delegates():
    respx.get(f"{BASE}/search").mock(return_value=httpx.Response(200, json=make_search_response()))
    async with OpenData() as client:
        result = await client.search("inflation")
        assert len(result.results) == 1


@respx.mock
async def test_suggest_delegates():
    respx.get(f"{BASE}/search/suggest").mock(
        return_value=httpx.Response(200, json=make_suggest_response())
    )
    async with OpenData() as client:
        result = await client.suggest("inf")
        assert isinstance(result, SuggestResponse)


@respx.mock
async def test_datasets_list():
    respx.get(f"{BASE}/datasets").mock(return_value=httpx.Response(200, json=make_dataset_list()))
    async with OpenData() as client:
        result = await client.datasets.list()
        items = [item async for item in result]
        assert len(items) == 1
        assert items[0].name == "CPI-U"


@respx.mock
async def test_datasets_get():
    respx.get(f"{BASE}/datasets/bls/cpi-u/meta").mock(
        return_value=httpx.Response(200, json=make_dataset_meta())
    )
    async with OpenData() as client:
        meta = await client.datasets.get("bls/cpi-u")
        assert meta.name == "CPI-U"


@respx.mock
async def test_datasets_query():
    respx.get(f"{BASE}/datasets/bls/cpi-u").mock(
        return_value=httpx.Response(200, json=make_data_page())
    )
    async with OpenData() as client:
        result = await client.datasets.query("bls/cpi-u")
        assert len(result) == 2


@respx.mock
async def test_datasets_query_all():
    page1 = make_data_page(rows=[[2020, 1.5]], next_cursor="c1", total_rows=2)
    page2 = make_data_page(rows=[[2021, 2.3]], next_cursor=None, total_rows=2)
    respx.get(f"{BASE}/datasets/bls/cpi-u").mock(
        side_effect=[
            httpx.Response(200, json=page1),
            httpx.Response(200, json=page2),
        ]
    )
    async with OpenData() as client:
        result = await client.datasets.query_all("bls/cpi-u")
        assert len(result) == 2


@respx.mock
async def test_datasets_create():
    respx.post(f"{BASE}/datasets").mock(return_value=httpx.Response(201, json=make_dataset_meta()))
    async with OpenData() as client:
        meta = await client.datasets.create({"source_url": "https://example.com"})
        assert meta.name == "CPI-U"


@respx.mock
async def test_datasets_delete():
    route = respx.delete(f"{BASE}/datasets/bls/cpi-u").mock(return_value=httpx.Response(204))
    async with OpenData() as client:
        await client.datasets.delete("bls/cpi-u")
        assert route.called


async def test_repr():
    client = OpenData()
    r = repr(client)
    assert "async=True" in r
    assert "api.tryopendata.ai" in r
    await client.close()


async def test_sql_property():
    client = OpenData()
    assert isinstance(client.sql, AsyncSqlResource)
    await client.close()


@respx.mock
async def test_sql_execute_delegates():
    route = respx.post(f"{BASE}/datasets/fred/gdp/query").mock(
        return_value=httpx.Response(200, json=make_sql_page())
    )
    async with OpenData() as client:
        result = await client.sql.execute("SELECT * FROM fred/gdp")
        assert isinstance(result, SqlResult)
        assert route.called
