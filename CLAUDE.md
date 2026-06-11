# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

`tryopendata` - Python SDK for the OpenData API. Published on PyPI as `tryopendata`. Built with Hatchling, managed with `uv`. Supports Python 3.10+.

## Commands

```bash
# Install all deps (including dev + optional extras)
uv sync --all-groups --all-extras

# Lint
uv run ruff check src/ tests/

# Format check
uv run ruff format --check src/ tests/

# Auto-fix lint + format
uv run ruff check --fix src/ tests/ && uv run ruff format src/ tests/

# Type check (strict mode, pydantic plugin)
uv run mypy src/

# Tests with coverage (80% minimum)
uv run pytest --cov=opendata_sdk --cov-report=term-missing --cov-fail-under=80

# Single test
uv run pytest tests/test_query.py::test_eq_filter -v
```

CI runs: lint -> format -> mypy -> pytest (matrix: 3.10, 3.11, 3.12). All must pass before merge.

## Architecture

Source lives in `src/opendata_sdk/`. The SDK provides both sync and async clients with identical APIs.

**Client layer** (`client.py`, `aio/client.py`): Entry points exposing resource properties (`.datasets`, `.search`, `.providers`, `.categories`) and convenience methods (`.meta()`, `.query()`, `.load()`, `.search()`). Both support context managers.

**Resources** (`_resources/`): One class per API endpoint type. Each has sync and async variants. `_base.py` holds shared helpers for param building and response parsing.

**Query builder** (`_query.py`): Immutable frozen dataclass with fluent interface. Every operation (`.filter()`, `.eq()`, `.sort()`, `.limit()`, `.group_by()`, `.aggregate()`) returns a new instance. Compiles to URL params via `_to_params()`.

**Transport** (`_transport.py`): Wraps httpx with automatic retries on 429/5xx using exponential backoff. Maps HTTP status codes to the exception hierarchy in `_exceptions.py`.

**DataResult** (`_result.py`): Wraps API responses (which use column-major format) and provides `.rows`, `.to_pandas()`, `.to_polars()` with automatic DuckDB-to-pandas/polars type mapping.

**Pagination** (`_pagination.py`): `PaginatedList[T]` and `AsyncPaginatedList[T]` handle transparent multi-page iteration.

**Types** (`_types.py`): Pydantic v2 models with `extra="ignore"` for forward compatibility.

## Key Patterns

- **Sync/async parity**: Both clients expose the same API surface. When adding features, implement in both.
- **Immutable queries**: Query is a frozen dataclass. Never mutate, always return new instances.
- **Column-major responses**: The API returns data as arrays of columns, not rows. `DataResult` handles the transpose.
- **Conventional commits**: Use `fix:`, `feat:`, `chore:`, `docs:` prefixes. Versioning is automated from commit messages (breaking = major, feat = minor, fix = patch).
- **Releases are automated**: CI success on main triggers version bump, tag, GitHub release, and PyPI publish. Don't manually bump versions.

## Testing

Tests use `respx` to mock HTTP responses (no real API calls). Test data factories (`make_dataset`, `make_data_page`, etc.) are in `conftest.py`. Async tests run automatically via `asyncio_mode = "auto"`.

## Ruff Config

Line length: 100. Target: py310. Lint rules: E, W, F, I, B, C4, UP, ARG, SIM.
