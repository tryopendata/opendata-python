from __future__ import annotations

from opendata_sdk._pagination import AsyncPaginatedList, PaginatedList

# ── Sync PaginatedList ───────────────────────────────────────────────


def test_iter_first_page():
    pl = PaginatedList(["a", "b", "c"], total=3, fetch_next=None, limit=20, offset=0)
    assert list(pl) == ["a", "b", "c"]


def test_auto_fetches_second_page():
    call_count = 0

    def fetch(_limit: int, _offset: int) -> tuple[list[str], int]:
        nonlocal call_count
        call_count += 1
        return ["d", "e"], 5

    pl = PaginatedList(["a", "b", "c"], total=5, fetch_next=fetch, limit=3, offset=0)
    items = list(pl)
    assert items == ["a", "b", "c", "d", "e"]
    assert call_count == 1


def test_multiple_pages():
    pages_data = [["d", "e", "f"], ["g"]]
    page_idx = 0

    def fetch(_limit: int, _offset: int) -> tuple[list[str], int]:
        nonlocal page_idx
        result = pages_data[page_idx] if page_idx < len(pages_data) else []
        page_idx += 1
        return result, 7

    pl = PaginatedList(["a", "b", "c"], total=7, fetch_next=fetch, limit=3, offset=0)
    assert list(pl) == ["a", "b", "c", "d", "e", "f", "g"]


def test_pages_yields_one_page_at_a_time():
    def fetch(_limit: int, _offset: int) -> tuple[list[str], int]:
        return ["d", "e"], 5

    pl = PaginatedList(["a", "b", "c"], total=5, fetch_next=fetch, limit=3, offset=0)
    pages = list(pl.pages())
    assert pages == [["a", "b", "c"], ["d", "e"]]


def test_len_returns_total():
    pl = PaginatedList(["a"], total=42, fetch_next=None, limit=20, offset=0)
    assert len(pl) == 42


def test_getitem():
    pl = PaginatedList(["a", "b", "c"], total=3, fetch_next=None, limit=20, offset=0)
    assert pl[0] == "a"
    assert pl[2] == "c"


def test_empty_first_page():
    pl = PaginatedList([], total=0, fetch_next=None, limit=20, offset=0)
    assert list(pl) == []
    assert len(pl) == 0


def test_fetch_next_returning_empty_stops():
    def fetch(_limit: int, _offset: int) -> tuple[list[str], int]:
        return [], 5

    pl = PaginatedList(["a", "b"], total=5, fetch_next=fetch, limit=2, offset=0)
    items = list(pl)
    assert items == ["a", "b"]


def test_no_fetch_next():
    """When fetch_next is None, only first page items are returned."""
    pl = PaginatedList(["a", "b"], total=10, fetch_next=None, limit=2, offset=0)
    assert list(pl) == ["a", "b"]


def test_repr():
    pl = PaginatedList(["a", "b"], total=5, fetch_next=None, limit=2, offset=0)
    r = repr(pl)
    assert "page_size=2" in r
    assert "total=5" in r


# ── Async PaginatedList ──────────────────────────────────────────────


async def test_async_iter_first_page():
    apl = AsyncPaginatedList(["a", "b"], total=2, fetch_next=None, limit=20, offset=0)
    items = [item async for item in apl]
    assert items == ["a", "b"]


async def test_async_auto_fetches():
    async def fetch(_limit: int, _offset: int) -> tuple[list[str], int]:
        return ["c", "d"], 4

    apl = AsyncPaginatedList(["a", "b"], total=4, fetch_next=fetch, limit=2, offset=0)
    items = [item async for item in apl]
    assert items == ["a", "b", "c", "d"]


async def test_async_pages():
    async def fetch(_limit: int, _offset: int) -> tuple[list[str], int]:
        return ["c"], 3

    apl = AsyncPaginatedList(["a", "b"], total=3, fetch_next=fetch, limit=2, offset=0)
    pages = [page async for page in apl.pages()]
    assert pages == [["a", "b"], ["c"]]


async def test_async_len():
    apl = AsyncPaginatedList(["a"], total=99, fetch_next=None, limit=20, offset=0)
    assert len(apl) == 99


async def test_async_empty():
    apl = AsyncPaginatedList([], total=0, fetch_next=None, limit=20, offset=0)
    items = [item async for item in apl]
    assert items == []


async def test_async_fetch_empty_stops():
    async def fetch(_limit: int, _offset: int) -> tuple[list[str], int]:
        return [], 5

    apl = AsyncPaginatedList(["a"], total=5, fetch_next=fetch, limit=1, offset=0)
    items = [item async for item in apl]
    assert items == ["a"]


async def test_async_repr():
    apl = AsyncPaginatedList(["a"], total=3, fetch_next=None, limit=1, offset=0)
    assert "AsyncPaginatedList" in repr(apl)
