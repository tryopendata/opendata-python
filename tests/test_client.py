from __future__ import annotations

import os
from unittest.mock import patch

import httpx
import respx

from opendata_sdk import OpenData
from opendata_sdk._resources.categories import CategoryResource
from opendata_sdk._resources.datasets import DatasetResource
from opendata_sdk._resources.providers import ProviderResource
from opendata_sdk._resources.sql import SqlResource
from opendata_sdk._result import SqlResult

from .conftest import make_search_response, make_sql_page

BASE = "https://api.tryopendata.ai/v1"


def test_constructor_with_api_key():
    client = OpenData(api_key="sk-test")
    assert client._transport._config.api_key == "sk-test"
    client.close()


def test_constructor_reads_env_var():
    with patch.dict(os.environ, {"OPENDATA_API_KEY": "sk-from-env"}):
        client = OpenData()
        assert client._transport._config.api_key == "sk-from-env"
        client.close()


def test_constructor_explicit_key_overrides_env():
    with patch.dict(os.environ, {"OPENDATA_API_KEY": "sk-from-env"}):
        client = OpenData(api_key="sk-explicit")
        assert client._transport._config.api_key == "sk-explicit"
        client.close()


def test_default_base_url():
    client = OpenData()
    assert client._transport._config.base_url == "https://api.tryopendata.ai/v1"
    client.close()


def test_custom_base_url():
    client = OpenData(base_url="https://custom.api.com/v2")
    assert client._transport._config.base_url == "https://custom.api.com/v2"
    client.close()


def test_datasets_property():
    client = OpenData()
    assert isinstance(client.datasets, DatasetResource)
    client.close()


def test_providers_property():
    client = OpenData()
    assert isinstance(client.providers, ProviderResource)
    client.close()


def test_categories_property():
    client = OpenData()
    assert isinstance(client.categories, CategoryResource)
    client.close()


@respx.mock
def test_search_delegates():
    respx.get(f"{BASE}/search").mock(return_value=httpx.Response(200, json=make_search_response()))
    client = OpenData()
    result = client.search("inflation")
    assert result.total == 1
    client.close()


@respx.mock
def test_context_manager():
    respx.get(f"{BASE}/search").mock(return_value=httpx.Response(200, json=make_search_response()))
    with OpenData() as client:
        result = client.search("test")
        assert result.total == 1


def test_repr():
    client = OpenData()
    assert "api.tryopendata.ai" in repr(client)
    client.close()


def test_custom_timeout():
    client = OpenData(timeout=60.0)
    assert client._transport._config.timeout == 60.0
    client.close()


def test_custom_max_retries():
    client = OpenData(max_retries=5)
    assert client._transport._config.max_retries == 5
    client.close()


def test_sql_property():
    client = OpenData()
    assert isinstance(client.sql, SqlResource)
    client.close()


@respx.mock
def test_sql_execute_delegates():
    route = respx.post(f"{BASE}/datasets/fred/gdp/query").mock(
        return_value=httpx.Response(200, json=make_sql_page())
    )
    client = OpenData()
    result = client.sql.execute("SELECT * FROM fred/gdp")
    assert isinstance(result, SqlResult)
    assert route.called
    client.close()
