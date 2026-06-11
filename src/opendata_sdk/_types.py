from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Dataset(BaseModel):
    """Dataset summary from list endpoints."""

    model_config = ConfigDict(extra="ignore")

    id: str
    name: str
    slug: str | None = None
    display_name: str | None = None
    description: str | None = None
    path: str
    provider: str | None = None
    status: str
    format: str | None = None
    rows: int | None = None
    star_count: int | None = None
    category: str | None = None
    created_at: datetime
    updated_at: datetime

    def __repr__(self) -> str:
        rows = f"{self.rows:,}" if self.rows is not None else "?"
        return f"Dataset({self.path!r}, rows={rows}, status={self.status!r})"


class ColumnStats(BaseModel):
    """Column-level statistics."""

    model_config = ConfigDict(extra="ignore")

    name: str
    type: str
    raw_type: str | None = None
    distinct_count: int | None = None
    null_count: int | None = None
    min: Any | None = None
    max: Any | None = None
    sample_values: list[Any] | None = None


class ViewInfo(BaseModel):
    """Available view on a dataset."""

    model_config = ConfigDict(extra="ignore")

    name: str
    description: str | None = None
    capabilities: list[str] = Field(default_factory=list)
    example_url: str | None = None


class DatasetMeta(Dataset):
    """Full dataset metadata from /meta endpoint."""

    source_url: str | None = None
    schema_info: dict[str, Any] | None = None
    available_views: list[ViewInfo] | None = None
    default_view: str | None = None
    semantic_entity: str | None = None
    semantic_time: str | None = None
    semantic_value: str | None = None
    time_granularity: str | None = None
    parquet_size_bytes: int | None = None
    canonical_questions: list[str] | None = None
    ask_cards: list[dict[str, Any]] | None = None
    kpi_snapshot: dict[str, Any] | None = None
    license: str | None = None
    landing_url: str | None = None
    source_count: int | None = None
    connector: str | None = None
    enrichment_status: str | None = None

    @property
    def columns(self) -> list[ColumnStats]:
        if not self.schema_info:
            return []
        return [ColumnStats.model_validate(c) for c in self.schema_info.get("columns", [])]

    def _repr_html_(self) -> str | None:
        try:
            name = self.display_name or self.name
            rows_str = f"{self.rows:,}" if self.rows is not None else "unknown"
            desc = self.description or ""

            cols_html = ""
            if self.schema_info:
                columns = self.schema_info.get("columns", [])
                if columns:
                    col_rows = ""
                    for col in columns[:20]:
                        col_name = col.get("name", "")
                        col_type = col.get("type", "")
                        col_desc = col.get("description", "")
                        col_rows += (
                            f"<tr>"
                            f"<td style='padding:3px 8px;font-family:monospace'>{col_name}</td>"
                            f"<td style='padding:3px 8px;color:#888'>{col_type}</td>"
                            f"<td style='padding:3px 8px;color:#555'>{col_desc}</td>"
                            f"</tr>"
                        )
                    if len(columns) > 20:
                        col_rows += (
                            f"<tr><td colspan='3' style='padding:3px 8px;color:#888'>"
                            f"... and {len(columns) - 20} more columns</td></tr>"
                        )
                    cols_html = (
                        f"<table style='border-collapse:collapse;margin-top:8px;font-size:13px'>"
                        f"<tr style='border-bottom:1px solid #ddd'>"
                        f"<th style='padding:3px 8px;text-align:left'>Column</th>"
                        f"<th style='padding:3px 8px;text-align:left'>Type</th>"
                        f"<th style='padding:3px 8px;text-align:left'>Description</th>"
                        f"</tr>{col_rows}</table>"
                    )

            return (
                f"<div style='font-family:sans-serif'>"
                f"<strong>{name}</strong> "
                f"<span style='color:#888'>({self.path})</span><br>"
                f"<span style='color:#555;font-size:13px'>{rows_str} rows</span>"
                + (f"<br><span style='color:#555;font-size:13px'>{desc}</span>" if desc else "")
                + cols_html
                + "</div>"
            )
        except Exception:
            return None


class DataPage(BaseModel):
    """Columnar data response from data endpoint."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    columns: list[str] = Field(default_factory=list)
    column_types: list[str] = Field(default_factory=list, alias="types")
    data: list[list[Any]] = Field(default_factory=list, alias="rows")
    total_rows: int | None = None
    filtered_rows: int | None = None
    limit: int | None = None
    offset: int | None = None
    next_cursor: str | None = None
    view: str | None = None
    warnings: list[dict[str, Any]] = Field(default_factory=list)


class SqlPage(BaseModel):
    """SQL query response in columnar format."""

    model_config = ConfigDict(extra="ignore")

    columns: list[str] = Field(default_factory=list)
    types: list[str] = Field(default_factory=list)
    rows: list[list[Any]] = Field(default_factory=list)
    row_count: int = 0
    execution_time_ms: float = 0.0
    truncated: bool = False
    warnings: list[str] | None = None

    def to_data_page(self) -> DataPage:
        """Convert to a DataPage for use with DataResult."""
        return DataPage(
            columns=self.columns,
            column_types=self.types,
            data=self.rows,
            total_rows=self.row_count,
        )


class SearchResult(BaseModel):
    """A single search result."""

    model_config = ConfigDict(extra="ignore")

    id: str
    name: str
    display_name: str | None = None
    slug: str
    provider: str | None = None
    path: str
    description: str | None = None
    status: str | None = None
    rows: int | None = None
    format: str | None = None
    relevance: float | None = None
    highlights: dict[str, str] | None = None
    categories: list[str] = Field(default_factory=list)
    star_count: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class SearchResponse(BaseModel):
    """Paginated search response."""

    model_config = ConfigDict(extra="ignore")

    results: list[SearchResult] = Field(default_factory=list)
    total: int = 0
    limit: int = 20
    offset: int = 0
    facets: dict[str, Any] | None = None
    query: str | None = None
    processing_time_ms: float | None = None


class SuggestResponse(BaseModel):
    """Autocomplete suggestion response."""

    model_config = ConfigDict(extra="ignore")

    suggestions: list[dict[str, Any]] = Field(default_factory=list)
    query: str | None = None


class Provider(BaseModel):
    """Data provider metadata."""

    model_config = ConfigDict(extra="ignore")

    id: str
    slug: str
    name: str
    description: str | None = None
    dataset_count: int | None = None
    total_rows: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class Category(BaseModel):
    """Dataset category."""

    model_config = ConfigDict(extra="ignore")

    slug: str
    name: str
    description: str | None = None
    dataset_count: int | None = None
    icon: str | None = None
