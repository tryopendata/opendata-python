from __future__ import annotations

import httpx
import respx

from opendata_sdk import OpenData
from opendata_sdk._types import SearchResponse, SuggestResponse

from .conftest import make_search_response, make_suggest_response

BASE = "https://api.tryopendata.ai/v1"


@respx.mock
def test_search_makes_get_with_q():
    route = respx.get(f"{BASE}/search").mock(
        return_value=httpx.Response(200, json=make_search_response())
    )
    client = OpenData()
    result = client.search("inflation")
    assert isinstance(result, SearchResponse)
    assert len(result.results) == 1
    assert result.results[0].name == "CPI-U"
    url = str(route.calls.last.request.url)
    assert "q=inflation" in url
    client.close()


@respx.mock
def test_search_with_all_params():
    route = respx.get(f"{BASE}/search").mock(
        return_value=httpx.Response(200, json=make_search_response())
    )
    client = OpenData()
    client.search(
        "inflation",
        mode="semantic",
        provider="bls",
        category="economics",
        sort="relevance",
        limit=10,
        offset=5,
    )
    url = str(route.calls.last.request.url)
    assert "mode=semantic" in url
    assert "provider=bls" in url
    assert "category=economics" in url
    assert "sort=relevance" in url
    assert "limit=10" in url
    assert "offset=5" in url
    client.close()


@respx.mock
def test_suggest_makes_get_suggest():
    route = respx.get(f"{BASE}/search/suggest").mock(
        return_value=httpx.Response(200, json=make_suggest_response())
    )
    client = OpenData()
    result = client.suggest("inf")
    assert isinstance(result, SuggestResponse)
    assert len(result.suggestions) == 1
    url = str(route.calls.last.request.url)
    assert "q=inf" in url
    client.close()


@respx.mock
def test_suggest_with_limit():
    route = respx.get(f"{BASE}/search/suggest").mock(
        return_value=httpx.Response(200, json=make_suggest_response())
    )
    client = OpenData()
    client.suggest("inf", limit=3)
    url = str(route.calls.last.request.url)
    assert "limit=3" in url
    client.close()


@respx.mock
def test_search_empty_results():
    respx.get(f"{BASE}/search").mock(
        return_value=httpx.Response(
            200,
            json={"results": [], "total": 0, "limit": 20, "offset": 0},
        )
    )
    client = OpenData()
    result = client.search("nonexistent")
    assert result.total == 0
    assert result.results == []
    client.close()
