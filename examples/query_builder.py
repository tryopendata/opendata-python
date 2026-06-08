"""Query builder features: filters, sort, aggregation, views."""

from opendata_sdk import OpenData, Query

client = OpenData()

# Basic filtering with convenience methods
q = (
    Query()
    .eq("state", "California")
    .gte("year", 2020)
    .fields("year", "state", "population")
    .sort("year", desc=True)
    .limit(50)
)
result = client.datasets.query("census/population", q)
print(f"California population data: {len(result)} rows")
for row in result.rows[:3]:
    print(f"  {row}")

# Filter with IN operator
print("\n--- Multiple states ---")
q = (
    Query()
    .isin("state", ["California", "Texas", "New York"])
    .gte("year", 2022)
    .sort("population", desc=True)
)
result = client.datasets.query("census/population", q)
for row in result.rows[:5]:
    print(f"  {row}")

# LIKE pattern matching
print("\n--- States matching 'New%' ---")
q = Query().like("state", "New%").sort("state")
result = client.datasets.query("census/population", q)
for row in result.rows[:5]:
    print(f"  {row}")

# Aggregation with group_by
print("\n--- Population by state (aggregated) ---")
q = (
    Query()
    .group_by("state")
    .aggregate("sum:population", "count:year")
    .sort("sum_population", desc=True)
    .limit(10)
)
result = client.datasets.query("census/population", q)
for row in result.rows:
    print(f"  {row}")

# Using a dataset view
print("\n--- Annual view ---")
q = Query().view("annual").filter("year", "gte", 2020)
result = client.datasets.query("bls/cpi-u", q)
for row in result.rows[:5]:
    print(f"  {row}")

# Queries are immutable, so you can reuse a base query
base = Query().gte("year", 2020).sort("year", desc=True).limit(10)
ca_query = base.eq("state", "California")
tx_query = base.eq("state", "Texas")

print("\n--- Reused base query for CA ---")
result = client.datasets.query("census/population", ca_query)
print(f"  {len(result)} rows")

print("\n--- Reused base query for TX ---")
result = client.datasets.query("census/population", tx_query)
print(f"  {len(result)} rows")

client.close()
