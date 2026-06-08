from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable, Iterator
from typing import Generic, TypeVar

T = TypeVar("T")


class PaginatedList(Generic[T]):
    """Auto-paginating list that fetches pages on demand (Stripe pattern).

    Iterating yields all items across pages transparently. Use .pages()
    to get one page at a time for batch processing.
    """

    def __init__(
        self,
        first_page_items: list[T],
        total: int,
        fetch_next: Callable[[int, int], tuple[list[T], int]] | None,
        limit: int,
        offset: int,
    ) -> None:
        self._current_items = first_page_items
        self._total = total
        self._fetch_next = fetch_next
        self._limit = limit
        self._offset = offset

    def _has_more(self) -> bool:
        return self._fetch_next is not None and self._offset + self._limit < self._total

    def __iter__(self) -> Iterator[T]:
        """Yield items, fetching next pages transparently."""
        yield from self._current_items
        while self._has_more():
            self._offset += self._limit
            assert self._fetch_next is not None
            items, _ = self._fetch_next(self._limit, self._offset)
            if not items:
                break
            yield from items

    def __len__(self) -> int:
        return self._total

    def __getitem__(self, index: int) -> T:
        """Access items on the current page by index. Does not auto-paginate."""
        n = len(self._current_items)
        if index >= n or index < -n:
            raise IndexError(
                f"Index {index} is out of range for the current page ({n} items). "
                f"Use iteration or .pages() to access all {self._total} items."
            )
        return self._current_items[index]

    def pages(self) -> Iterator[list[T]]:
        """Yield one page at a time."""
        yield self._current_items
        while self._has_more():
            self._offset += self._limit
            assert self._fetch_next is not None
            items, _ = self._fetch_next(self._limit, self._offset)
            if not items:
                break
            yield items

    def __repr__(self) -> str:
        return f"PaginatedList(page_size={len(self._current_items)}, total={self._total})"


class AsyncPaginatedList(Generic[T]):
    """Async auto-paginating list that fetches pages on demand.

    Use ``async for item in paginated_list`` to iterate all items,
    or ``async for page in paginated_list.pages()`` for batch processing.
    """

    def __init__(
        self,
        first_page_items: list[T],
        total: int,
        fetch_next: Callable[[int, int], Awaitable[tuple[list[T], int]]] | None,
        limit: int,
        offset: int,
    ) -> None:
        self._current_items = first_page_items
        self._total = total
        self._fetch_next = fetch_next
        self._limit = limit
        self._offset = offset

    def _has_more(self) -> bool:
        return self._fetch_next is not None and self._offset + self._limit < self._total

    async def __aiter__(self) -> AsyncIterator[T]:
        """Yield items, fetching next pages transparently."""
        for item in self._current_items:
            yield item
        while self._has_more():
            self._offset += self._limit
            assert self._fetch_next is not None
            items, _ = await self._fetch_next(self._limit, self._offset)
            if not items:
                break
            for item in items:
                yield item

    def __len__(self) -> int:
        return self._total

    async def pages(self) -> AsyncIterator[list[T]]:
        """Yield one page at a time."""
        yield self._current_items
        while self._has_more():
            self._offset += self._limit
            assert self._fetch_next is not None
            items, _ = await self._fetch_next(self._limit, self._offset)
            if not items:
                break
            yield items

    def __repr__(self) -> str:
        return f"AsyncPaginatedList(page_size={len(self._current_items)}, total={self._total})"
