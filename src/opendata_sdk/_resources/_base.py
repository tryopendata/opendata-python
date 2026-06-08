from __future__ import annotations

from typing import Any

from opendata_sdk._result import DataResult
from opendata_sdk._types import DataPage, Dataset


class BaseDatasetResource:
    """Shared logic for building params and parsing responses.

    Sync and async resource classes call these static helpers
    so the actual HTTP plumbing stays in the subclasses.
    """

    @staticmethod
    def _build_list_params(
        provider: str | None = None,
        limit: int = 20,
        offset: int = 0,
        status: str | None = None,
        sort: str | None = None,
    ) -> tuple[str, dict[str, str]]:
        """Returns (path, params) for the list endpoint."""
        path = f"/datasets/{provider}" if provider else "/datasets"
        params: dict[str, str] = {"limit": str(limit), "offset": str(offset)}
        if status:
            params["status"] = status
        if sort:
            params["sort"] = sort
        return path, params

    @staticmethod
    def _build_query_params(
        path: str,
        query: Any = None,
        **kwargs: Any,
    ) -> tuple[str, dict[str, str]]:
        """Returns (api_path, params) for a data query."""
        parts = path.strip("/").split("/")
        if len(parts) != 2:
            raise ValueError(f"Path must be 'provider/dataset', got: {path}")
        api_path = f"/datasets/{parts[0]}/{parts[1]}"
        params: dict[str, str] = {"response_format": "columnar"}
        if query is not None:
            params.update(query._to_params())
        for k, v in kwargs.items():
            if v is not None:
                params[k] = str(v)
        return api_path, params

    @staticmethod
    def _parse_dataset_list(data: dict[str, Any]) -> tuple[list[Dataset], int]:
        """Parse a list response into Dataset objects and total count."""
        items = data.get("items", [])
        total = data.get("total", len(items))
        datasets = [Dataset.model_validate(d) for d in items]
        return datasets, total

    @staticmethod
    def _parse_data_result(data: dict[str, Any]) -> DataResult:
        """Parse a data response, detecting hierarchical datasets."""
        if "subdatasets" in data:
            slugs = [s.get("slug", s) if isinstance(s, dict) else s for s in data["subdatasets"]]
            raise ValueError(
                f"This is a hierarchical dataset with subdatasets: {slugs}. "
                f"Query a specific subdataset instead."
            )
        page = DataPage.model_validate(data)
        return DataResult(page)

    @staticmethod
    def _split_path(path: str) -> tuple[str, str]:
        """Split 'provider/dataset' into (provider, dataset)."""
        parts = path.strip("/").split("/")
        if len(parts) != 2:
            raise ValueError(f"Path must be 'provider/dataset', got: {path}")
        return parts[0], parts[1]
