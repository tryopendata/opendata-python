from __future__ import annotations

import os
from dataclasses import dataclass, field

DEFAULT_BASE_URL = "https://api.tryopendata.ai/v1"
DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 3


@dataclass
class ClientConfig:
    """Configuration for the OpenData SDK client."""

    base_url: str = DEFAULT_BASE_URL
    api_key: str | None = field(default=None)
    timeout: float = DEFAULT_TIMEOUT
    max_retries: int = DEFAULT_MAX_RETRIES

    def __post_init__(self) -> None:
        if self.api_key is None:
            self.api_key = os.environ.get("OPENDATA_API_KEY")
        self.base_url = self.base_url.rstrip("/")
