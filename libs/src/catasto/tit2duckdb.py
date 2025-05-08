import asyncio

from catasto.duckdb.entitlement import load_titolarita

if __name__ == "__main__":
    db_path = asyncio.run(
        load_titolarita(
            tit_filepath="/tmp/test.Tit",
            duckdb_filepath="/tmp/catasto.duckdb",
            clean_tables=True,
        )
    )
    print(f"Database path: {db_path}")
