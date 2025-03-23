import asyncio

from catasto.duckdb.land import load_terreni

if __name__ == "__main__":
    db_path = asyncio.run(
        load_terreni(
            fab_filepath="/tmp/test.Ter",
            duckdb_filepath="/tmp/catasto.duckdb",
            clean_db=True,
        )
    )
    print(f"Database path: {db_path}")
