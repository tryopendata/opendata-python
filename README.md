# opendata-sdk

Python client for the [OpenData API](https://tryopendata.ai). Query, search, and analyze open datasets with a few lines of code.

## Installation

```bash
pip install opendata-sdk
```

With DataFrame support:

```bash
pip install opendata-sdk[pandas]   # pandas
pip install opendata-sdk[polars]   # polars
pip install opendata-sdk[all]      # both
```

## Quick Start

```python
from opendata_sdk import OpenData

client = OpenData()  # or OpenData(api_key="od_live_...")
df = client.load("bls/cpi-u").to_pandas()
```

That's it. `load()` handles pagination automatically and returns a `DataResult` ready for conversion.

## Querying Data

Three entry points, each for a different use case:

| Method | Returns | When |
|--------|---------|------|
| `client.load(path)` | All rows, paginated automatically | Exploration, notebooks, analysis |
| `client.query(path)` | First page only (up to 10,000 rows) | Sampling, dashboards |
| `client.datasets.query_iter(path)` | One page at a time | Very large datasets |

```python
from opendata_sdk import OpenData

client = OpenData()

# Load everything -- the most common case
df = client.load("bls/cpi-u").to_pandas()

# Sample the first page for quick exploration
result = client.query("bls/cpi-u")
print(result.rows[:5])  # list of dicts, no extra deps needed
df = result.to_pandas()
df = result.to_polars()

# Process a huge dataset without loading it all into memory
for page in client.datasets.query_iter("bls/cpi-u", page_size=5000):
    df = page.to_pandas()
    process_batch(df)
```

### Schema Inspection

```python
# Inspect schema without converting to pandas
result = client.query("bls/cpi-u")
print(result.dtypes)   # {'year': 'BIGINT', 'value': 'DOUBLE', ...}
print(result.schema)   # [{'name': 'year', 'type': 'BIGINT'}, ...]
print(result.warnings) # API warnings (e.g. truncated results)
```

## Query Builder

The `Query` class gives you a fluent interface for filtering, sorting, and aggregating. Each method returns a new immutable query, so you can safely reuse and extend them.

```python
from opendata_sdk import OpenData, Query

client = OpenData()

q = (
    Query()
    .filter("year", "gte", 2020)
    .filter("state", "eq", "California")
    .sort("year", desc=True)
    .fields("year", "state", "population")
    .limit(100)
)

df = client.load("census/population", q).to_pandas()
```

### Filter Operators

```python
q = Query()
q.eq("state", "Texas")                    # state = 'Texas'
q.ne("status", "draft")                   # status != 'draft'
q.gt("year", 2020)                        # year > 2020
q.gte("year", 2020)                       # year >= 2020
q.lt("value", 1000)                       # value < 1000
q.lte("value", 1000)                      # value <= 1000
q.like("name", "%energy%")                # name LIKE '%energy%'
q.isin("state", ["CA", "TX", "NY"])       # state IN ('CA', 'TX', 'NY')
```

### Aggregation

```python
q = (
    Query()
    .group_by("state")
    .aggregate("sum:population", "count:id")
    .sort("sum_population", desc=True)
)

df = client.load("census/population", q).to_pandas()
```

### Views

Some datasets have pre-configured views with computed columns or joins:

```python
q = Query().view("annual").filter("year", "gte", 2015)
df = client.load("bls/cpi-u", q).to_pandas()
```

## Auto-Pagination

`client.datasets.list()` returns a `PaginatedList` that fetches pages transparently as you iterate:

```python
# Iterates through all datasets, fetching pages as needed
for dataset in client.datasets.list():
    print(f"{dataset.path}: {dataset.rows} rows")

# Or get one page at a time
paginated = client.datasets.list(limit=50)
for page in paginated.pages():
    print(f"Page with {len(page)} datasets")
```

## Search

```python
results = client.search("inflation consumer prices")
for hit in results.results:
    print(f"{hit.path} (relevance: {hit.relevance})")

# Filter by provider or category
results = client.search("population", provider="census", limit=5)

# Autocomplete suggestions
suggestions = client.suggest("infla")
```

## Dataset Metadata

```python
# Full metadata for a specific dataset (shortcut: client.meta())
meta = client.meta("census/population")
print(meta.description)
print(meta.rows)
print(meta.available_views)

# Column statistics
columns = client.datasets.columns("census/population")
for col in columns:
    print(f"{col.name}: {col.type} ({col.distinct_count} distinct)")

# Available views
views = client.datasets.views("bls/cpi-u")
for view in views:
    print(f"{view.name}: {view.description}")
```

## Providers and Categories

```python
# List all data providers
for provider in client.providers.list():
    print(f"{provider.slug}: {provider.dataset_count} datasets")

# List categories
for category in client.categories.list():
    print(f"{category.slug}: {category.name}")
```

## Async Usage

The async client mirrors the sync API exactly. Import from `opendata_sdk.aio`:

```python
import asyncio
from opendata_sdk.aio import OpenData

async def main():
    async with OpenData() as client:
        result = await client.datasets.query("census/population")
        df = result.to_pandas()

        # Auto-pagination works with async for
        async for dataset in await client.datasets.list():
            print(dataset.name)

asyncio.run(main())
```

## Error Handling

All errors inherit from `OpenDataError`, so you can catch broadly or target specific cases:

```python
from opendata_sdk import OpenData, NotFoundError, RateLimitError, OpenDataError

client = OpenData()

try:
    result = client.datasets.query("nonexistent/dataset")
except NotFoundError:
    print("Dataset doesn't exist")
except RateLimitError as e:
    print(f"Throttled. Retry after {e.retry_after}s")
except OpenDataError as e:
    print(f"API error {e.status_code}: {e.message}")
```

The full exception hierarchy:

| Exception | Status Code | When |
|-----------|-------------|------|
| `AuthenticationError` | 401 | Missing or invalid API key |
| `ForbiddenError` | 403 | Insufficient permissions |
| `NotFoundError` | 404 | Dataset or resource not found |
| `InvalidRequestError` | 400, 422 | Bad request parameters |
| `RateLimitError` | 429 | Too many requests |
| `APIError` | 5xx | Server error |
| `APIConnectionError` | - | Network or timeout failure |

The SDK automatically retries on 429 and 5xx responses with exponential backoff (configurable via `max_retries`).

## Configuration

```python
client = OpenData(
    api_key="od_live_...",          # or set OPENDATA_API_KEY env var
    base_url="https://...",    # default: https://api.tryopendata.ai/v1
    timeout=60.0,              # request timeout in seconds (default: 30)
    max_retries=5,             # retry attempts on 429/5xx (default: 3)
)
```

The API key can also be set via the `OPENDATA_API_KEY` environment variable. If both are provided, the constructor argument takes priority.

## Context Manager

Both sync and async clients support context managers to ensure the HTTP connection is properly closed:

```python
# Sync
with OpenData() as client:
    result = client.datasets.query("census/population")

# Async
async with OpenData() as client:
    result = await client.datasets.query("census/population")
```

## License

Apache-2.0
