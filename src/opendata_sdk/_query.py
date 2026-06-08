from __future__ import annotations

import dataclasses
import logging
import re
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("opendata_sdk")

# Pattern for valid API column names
_COLUMN_PATTERN = re.compile(r"^[a-z_][a-z0-9_]*$")


def _validate_column(name: str) -> str:
    """Warn if a column name doesn't match the API's expected format."""
    if not _COLUMN_PATTERN.match(name):
        logger.warning(
            "Column name %r contains uppercase or special characters. "
            "The API only supports lowercase column names matching [a-z_][a-z0-9_]*.",
            name,
        )
    return name


@dataclass(frozen=True)
class _Filter:
    column: str
    operator: str  # "eq", "ne", "gt", "gte", "lt", "lte", "like", "in"
    value: Any


@dataclass(frozen=True)
class _Sort:
    column: str
    desc: bool = False


@dataclass(frozen=True)
class Query:
    """Fluent, immutable query builder for the OpenData data API.

    Each method returns a new Query instance so you can chain calls
    without mutating the original. Queries are frozen — mutations are
    impossible and the immutability contract is enforced by the runtime.

    Example::

        q = (
            Query()
            .filter("year", "gte", 2020)
            .eq("state", "California")
            .sort("year", desc=True)
            .fields("year", "state", "population")
            .limit(100)
        )

    Aggregate expressions use colon syntax: ``"sum:column"``, ``"count:column"``::

        q = Query().group_by("state").aggregate("sum:population", "count:year")
    """

    _fields: tuple[str, ...] = field(default_factory=tuple)
    _filters: tuple[_Filter, ...] = field(default_factory=tuple)
    _sorts: tuple[_Sort, ...] = field(default_factory=tuple)
    _limit_val: int | None = None
    _offset_val: int | None = None
    _view_name: str | None = None
    _group_by_col: str | None = None
    _aggregates: tuple[str, ...] = field(default_factory=tuple)

    # --- Column selection ---

    def fields(self, *columns: str) -> Query:
        """Select specific columns to return."""
        return dataclasses.replace(self, _fields=tuple(_validate_column(c) for c in columns))

    # --- Filters ---

    def filter(self, column: str, operator: str, value: Any) -> Query:
        """Add a filter with an explicit operator."""
        new_filter = _Filter(_validate_column(column), operator, value)
        return dataclasses.replace(self, _filters=(*self._filters, new_filter))

    def eq(self, column: str, value: Any) -> Query:
        """Filter where column equals value."""
        return self.filter(column, "eq", value)

    def ne(self, column: str, value: Any) -> Query:
        """Filter where column does not equal value."""
        return self.filter(column, "ne", value)

    def gt(self, column: str, value: Any) -> Query:
        """Filter where column is greater than value."""
        return self.filter(column, "gt", value)

    def gte(self, column: str, value: Any) -> Query:
        """Filter where column is greater than or equal to value."""
        return self.filter(column, "gte", value)

    def lt(self, column: str, value: Any) -> Query:
        """Filter where column is less than value."""
        return self.filter(column, "lt", value)

    def lte(self, column: str, value: Any) -> Query:
        """Filter where column is less than or equal to value."""
        return self.filter(column, "lte", value)

    def like(self, column: str, pattern: str) -> Query:
        """Filter where column matches a LIKE pattern."""
        return self.filter(column, "like", pattern)

    def isin(self, column: str, values: list[Any]) -> Query:
        """Filter where column value is in the given list."""
        return self.filter(column, "in", values)

    # --- Sorting ---

    def sort(self, column: str, desc: bool = False) -> Query:
        """Add a sort clause."""
        new_sort = _Sort(_validate_column(column), desc)
        return dataclasses.replace(self, _sorts=(*self._sorts, new_sort))

    # --- Pagination ---

    def limit(self, n: int) -> Query:
        """Set the maximum number of rows to return."""
        return dataclasses.replace(self, _limit_val=n)

    def offset(self, n: int) -> Query:
        """Set the row offset for pagination."""
        return dataclasses.replace(self, _offset_val=n)

    # --- View ---

    def view(self, name: str) -> Query:
        """Select a dataset view."""
        return dataclasses.replace(self, _view_name=name)

    # --- Aggregation ---

    def group_by(self, column: str) -> Query:
        """Group results by a column."""
        return dataclasses.replace(self, _group_by_col=_validate_column(column))

    def aggregate(self, *exprs: str) -> Query:
        """Add aggregate expressions using colon syntax: ``"sum:column"``, ``"count:column"``.

        Appends to any existing aggregates (consistent with filter/sort chaining).

        Example::

            Query().group_by("state").aggregate("sum:population", "count:year")
        """
        return dataclasses.replace(self, _aggregates=(*self._aggregates, *exprs))

    # --- Compile to params ---

    def _to_params(self) -> dict[str, str]:
        """Compile the query into URL query parameters.

        Filter syntax uses brackets:
          - eq:    filter[column]=value
          - other: filter[column][operator]=value
          - in:    filter[column][in]=val1,val2,val3
        """
        params: dict[str, str] = {}

        # Fields
        if self._fields:
            params["fields"] = ",".join(self._fields)

        # Filters
        for f in self._filters:
            if f.operator == "eq":
                key = f"filter[{f.column}]"
            else:
                key = f"filter[{f.column}][{f.operator}]"

            if f.operator == "in" and isinstance(f.value, list):
                params[key] = ",".join(str(v) for v in f.value)
            else:
                params[key] = str(f.value)

        # Sort
        if self._sorts:
            # Multiple sorts: comma-separated, desc gets a - prefix
            parts = []
            for s in self._sorts:
                parts.append(f"-{s.column}" if s.desc else s.column)
            params["sort"] = ",".join(parts)

        # Pagination
        if self._limit_val is not None:
            params["limit"] = str(self._limit_val)
        if self._offset_val is not None:
            params["offset"] = str(self._offset_val)

        # View
        if self._view_name is not None:
            params["view"] = self._view_name

        # Aggregation
        if self._group_by_col is not None:
            params["group_by"] = self._group_by_col
        if self._aggregates:
            params["aggregate"] = ",".join(self._aggregates)

        return params

    def __repr__(self) -> str:
        parts = []
        if self._fields:
            parts.append(f"fields={list(self._fields)}")
        if self._filters:
            parts.append(f"filters={len(self._filters)}")
        if self._sorts:
            parts.append(f"sorts={len(self._sorts)}")
        if self._limit_val is not None:
            parts.append(f"limit={self._limit_val}")
        if self._offset_val is not None:
            parts.append(f"offset={self._offset_val}")
        if self._view_name:
            parts.append(f"view={self._view_name}")
        return f"Query({', '.join(parts) if parts else 'empty'})"
