from __future__ import annotations

import logging
from functools import cached_property
from typing import TYPE_CHECKING, Any

from opendata_sdk._types import DataPage

if TYPE_CHECKING:
    import pandas as pd
    import polars as pl

logger = logging.getLogger("opendata_sdk")

# Mapping from DuckDB/API column types to pandas nullable dtypes
_PANDAS_TYPE_MAP: dict[str, str] = {
    "VARCHAR": "string",
    "TEXT": "string",
    "STRING": "string",
    "BIGINT": "Int64",
    "INTEGER": "Int64",
    "INT": "Int64",
    "SMALLINT": "Int64",
    "TINYINT": "Int64",
    "HUGEINT": "Int64",
    "DOUBLE": "Float64",
    "FLOAT": "Float64",
    "REAL": "Float64",
    "DECIMAL": "Float64",
    "BOOLEAN": "boolean",
    "BOOL": "boolean",
}

# Types that should be parsed as datetime in pandas
_PANDAS_DATETIME_TYPES = frozenset(
    {
        "DATE",
        "TIMESTAMP",
        "TIMESTAMP WITH TIME ZONE",
        "TIMESTAMP_S",
        "TIMESTAMP_MS",
        "TIMESTAMP_NS",
    }
)


class DataResult:
    """Wraps a DataPage and provides conversion methods.

    This is the primary way to work with query results. Access raw data
    via .rows (list of dicts) or convert to pandas/polars DataFrames.
    """

    def __init__(self, page: DataPage) -> None:
        self._page = page

    @property
    def columns(self) -> list[str]:
        """Column names from the response."""
        return self._page.columns

    @cached_property
    def rows(self) -> list[dict[str, Any]]:
        """Data as a list of dicts (zero-dependency).

        Transposes the columnar API response into row-oriented dicts.
        Computed once and cached.
        """
        cols = self._page.columns
        return [{cols[i]: val for i, val in enumerate(row)} for row in self._page.data]

    @property
    def total_rows(self) -> int | None:
        """Total row count in the dataset (not just this page)."""
        return self._page.total_rows

    @property
    def filtered_rows(self) -> int | None:
        """Row count after applying filters (not just this page)."""
        return self._page.filtered_rows

    @property
    def next_cursor(self) -> str | None:
        """Cursor for fetching the next page, if available."""
        return self._page.next_cursor

    @property
    def warnings(self) -> list[dict[str, Any]]:
        """API warnings for this response (e.g. truncated results, deprecated views)."""
        return self._page.warnings

    @property
    def dtypes(self) -> dict[str, str]:
        """Column name -> API type string (e.g. 'BIGINT', 'VARCHAR', 'DATE')."""
        return dict(zip(self._page.columns, self._page.column_types, strict=False))

    @property
    def schema(self) -> list[dict[str, str]]:
        """List of {'name', 'type'} dicts for quick schema inspection."""
        return [
            {"name": c, "type": t}
            for c, t in zip(self._page.columns, self._page.column_types, strict=False)
        ]

    def _repr_html_(self) -> str | None:
        """Jupyter HTML table display -- shows up to 10 rows with column types."""
        try:
            columns = self._page.columns
            column_types = self._page.column_types
            data = self._page.data

            if not columns:
                return None

            preview_rows = data[:10]
            total = self._page.total_rows
            n_shown = len(preview_rows)
            n_total = len(data)

            header_cells = "".join(
                "<th style='padding:4px 8px;border-bottom:2px solid currentColor;"
                "opacity:0.9;text-align:left'>"
                f"{col}<br><span style='font-weight:normal;opacity:0.5;font-size:11px'>"
                f"{column_types[i] if i < len(column_types) else ''}</span></th>"
                for i, col in enumerate(columns)
            )

            body_rows = ""
            for row in preview_rows:
                cells = "".join(
                    f"<td style='padding:4px 8px;border-bottom:1px solid rgba(128,128,128,0.2)'>"
                    f"{row[i] if i < len(row) else ''}</td>"
                    for i in range(len(columns))
                )
                body_rows += f"<tr>{cells}</tr>"

            footer = ""
            if total is not None and total > n_shown:
                footer = (
                    f"<tr><td colspan='{len(columns)}' "
                    f"style='padding:4px 8px;opacity:0.5;font-size:12px'>"
                    f"Showing {n_shown} of {total:,} total rows</td></tr>"
                )
            elif n_total > n_shown:
                footer = (
                    f"<tr><td colspan='{len(columns)}' "
                    f"style='padding:4px 8px;opacity:0.5;font-size:12px'>"
                    f"Showing {n_shown} of {n_total} rows in this page</td></tr>"
                )

            return (
                f"<div style='font-family:sans-serif;font-size:13px'>"
                f"<table style='border-collapse:collapse'>"
                f"<thead><tr>{header_cells}</tr></thead>"
                f"<tbody>{body_rows}{footer}</tbody>"
                f"</table></div>"
            )
        except Exception:
            return None

    def to_pandas(self) -> pd.DataFrame:
        """Convert to a pandas DataFrame. Requires opendata-sdk[pandas].

        Uses nullable dtypes (Int64, Float64, string, boolean) so that
        null values are preserved without silent type coercion.
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError(
                "pandas is required for to_pandas(). "
                "Install it with: pip install opendata-sdk[pandas]"
            ) from None

        columns = self._page.columns
        column_types = self._page.column_types
        data = self._page.data

        if not columns:
            return pd.DataFrame()

        # Build column-oriented dict from row arrays
        col_data: dict[str, list[Any]] = {col: [] for col in columns}
        for row in data:
            for i, col in enumerate(columns):
                col_data[col].append(row[i] if i < len(row) else None)

        df = pd.DataFrame(col_data)

        # Apply type coercion based on column_types from the API
        for i, col in enumerate(columns):
            if i >= len(column_types):
                continue
            col_type = column_types[i].upper()

            # Strip any precision info like DECIMAL(18,3)
            base_type = col_type.split("(")[0].strip()

            if base_type in _PANDAS_DATETIME_TYPES:
                df[col] = pd.to_datetime(df[col], errors="coerce")
            elif base_type in _PANDAS_TYPE_MAP:
                target_dtype = _PANDAS_TYPE_MAP[base_type]
                try:
                    df[col] = df[col].astype(target_dtype)  # type: ignore[call-overload]
                except (ValueError, TypeError):
                    logger.debug(
                        "Could not coerce column %r to %s, keeping original type",
                        col,
                        target_dtype,
                    )

        return df

    def to_polars(self) -> pl.DataFrame:
        """Convert to a polars DataFrame. Requires opendata-sdk[polars].

        Transposes row arrays into per-column lists and builds the DataFrame.
        """
        try:
            import polars as pl
        except ImportError:
            raise ImportError(
                "polars is required for to_polars(). "
                "Install it with: pip install opendata-sdk[polars]"
            ) from None

        columns = self._page.columns
        data = self._page.data

        if not columns:
            return pl.DataFrame()

        # Transpose rows into column-oriented dict
        col_data = {
            col: [row[i] if i < len(row) else None for row in data] for i, col in enumerate(columns)
        }

        return pl.DataFrame(col_data)

    def __len__(self) -> int:
        return len(self._page.data)

    def __repr__(self) -> str:
        return f"DataResult(rows={len(self)}, columns={len(self.columns)})"


class SqlResult(DataResult):
    """Wraps a SQL query response with additional metadata.

    Inherits all DataResult functionality (rows, to_pandas, to_polars)
    and adds SQL-specific properties like execution_time_ms and truncated.
    """

    def __init__(
        self,
        page: DataPage,
        *,
        execution_time_ms: float,
        truncated: bool,
        row_count: int,
        sql_warnings: list[str],
    ) -> None:
        super().__init__(page)
        self._execution_time_ms = execution_time_ms
        self._truncated = truncated
        self._row_count = row_count
        self._sql_warnings = sql_warnings

    @property
    def execution_time_ms(self) -> float:
        """Query execution time in milliseconds."""
        return self._execution_time_ms

    @property
    def truncated(self) -> bool:
        """Whether results were truncated due to row_limit."""
        return self._truncated

    @property
    def row_count(self) -> int:
        """Number of rows returned by the query."""
        return self._row_count

    @property
    def sql_warnings(self) -> list[str]:
        """SQL-specific warnings from query execution."""
        return self._sql_warnings

    def __repr__(self) -> str:
        return (
            f"SqlResult(rows={len(self)}, columns={len(self.columns)}, "
            f"time={self._execution_time_ms:.0f}ms)"
        )
