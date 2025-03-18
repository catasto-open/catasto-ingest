import asyncio

from catasto.duckdb.building import load_fabbricati

if __name__ == "__main__":
    db_path = asyncio.run(
        load_fabbricati(
            fab_filepath="/tmp/test.Fab",
            duckdb_filepath="/tmp/catasto.duckdb",
            clean_db=True,
        )
    )
    print(f"Database path: {db_path}")
