import asyncio

from catasto.duckdb.subject import load_soggetti

if __name__ == "__main__":
    db_path = asyncio.run(
        load_soggetti(
            sog_filepath="/tmp/test.Sog",
            duckdb_filepath="/tmp/catasto.duckdb",
            clean_tables=True,
        )
    )
    print(f"Database path: {db_path}")
