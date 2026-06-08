"""Fetch data and analyze it with pandas.

Requires: pip install opendata-sdk[pandas]
"""

from opendata_sdk import OpenData, Query

client = OpenData()

# Fetch CPI data for recent years
q = Query().filter("year", "gte", 2015).sort("year").sort("period")
result = client.datasets.query_all("bls/cpi-u", query=q, max_rows=10000)

df = result.to_pandas()
print(f"Fetched {len(df)} rows, {len(df.columns)} columns")
print(f"Columns: {list(df.columns)}")
print()

# Basic summary
print("--- Data types ---")
print(df.dtypes)
print()

# Group by year and compute average value
if "year" in df.columns and "value" in df.columns:
    yearly = df.groupby("year")["value"].mean()
    print("--- Average CPI by year ---")
    print(yearly)
    print()

    # Year-over-year change
    pct_change = yearly.pct_change() * 100
    print("--- Year-over-year % change ---")
    print(pct_change.dropna().round(2))

client.close()
