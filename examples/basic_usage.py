"""Basic usage of the OpenData SDK."""

from opendata_sdk import OpenData

client = OpenData()

# Search for datasets
results = client.search("population by state")
print(f"Found {results.total} datasets\n")
for hit in results.results[:3]:
    print(f"  {hit.path}: {hit.description}")

# List datasets from a specific provider
print("\n--- Census datasets ---")
for dataset in client.datasets.list(provider="census", limit=5):
    print(f"  {dataset.path} ({dataset.rows} rows)")

# Get metadata for a dataset
meta = client.datasets.get("census/population")
print(f"\n--- {meta.name} ---")
print(f"  Rows: {meta.rows}")
print(f"  Format: {meta.format}")
print(f"  Views: {meta.available_views}")

# Query data and get results as dicts (no extra dependencies)
result = client.datasets.query("census/population")
print(f"\n--- First 3 rows ({len(result)} total on this page) ---")
for row in result.rows[:3]:
    print(f"  {row}")

# Close the client when done
client.close()
