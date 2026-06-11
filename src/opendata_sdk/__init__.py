from __future__ import annotations

from opendata_sdk._exceptions import (
    APIConnectionError,
    APIError,
    AuthenticationError,
    ForbiddenError,
    InvalidRequestError,
    NotFoundError,
    OpenDataError,
    RateLimitError,
)
from opendata_sdk._pagination import AsyncPaginatedList, PaginatedList
from opendata_sdk._query import Query
from opendata_sdk._result import DataResult, SqlResult
from opendata_sdk._types import (
    Category,
    ColumnStats,
    DataPage,
    Dataset,
    DatasetMeta,
    Provider,
    SearchResponse,
    SearchResult,
    SqlPage,
    SuggestResponse,
    ViewInfo,
)
from opendata_sdk._version import __version__
from opendata_sdk.client import OpenData

__all__ = [
    # Version
    "__version__",
    # Client
    "OpenData",
    # Query + Result
    "Query",
    "DataResult",
    "SqlResult",
    # Pagination
    "AsyncPaginatedList",
    "PaginatedList",
    # Types
    "Category",
    "ColumnStats",
    "Dataset",
    "DatasetMeta",
    "Provider",
    "SearchResponse",
    "SearchResult",
    "SuggestResponse",
    "DataPage",
    "SqlPage",
    "ViewInfo",
    # Exceptions
    "APIConnectionError",
    "APIError",
    "AuthenticationError",
    "ForbiddenError",
    "InvalidRequestError",
    "NotFoundError",
    "OpenDataError",
    "RateLimitError",
]
