"""Async usage of the OpenData SDK."""

import asyncio

from opendata_sdk.aio import OpenData


async def main():
    async with OpenData() as client:
        # Search
        results = await client.search("consumer price index")
        print(f"Found {results.total} datasets")

        # List datasets with auto-pagination
        print("\n--- All BLS datasets ---")
        async for dataset in await client.datasets.list(provider="bls"):
            print(f"  {dataset.path}: {dataset.rows} rows")

        # Query data
        result = await client.datasets.query("bls/cpi-u")
        print(f"\n--- CPI-U data ({len(result)} rows) ---")
        for row in result.rows[:5]:
            print(f"  {row}")

        # Get metadata
        meta = await client.datasets.get("bls/cpi-u")
        print(f"\n--- {meta.name} ---")
        print(f"  Description: {meta.description}")
        print(f"  Total rows: {meta.rows}")


if __name__ == "__main__":
    asyncio.run(main())
