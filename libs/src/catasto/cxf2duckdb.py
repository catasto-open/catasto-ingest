import asyncio

from catasto.duckdb.carto import load_carto

if __name__ == "__main__":
    db_path = asyncio.run(
        load_carto(
            cxf_filepath="/tmp/test,cxf",
            duckdb_filepath="/tmp/catasto.duckdb",
            clean_tables=True,
        )
    )
    print(f"Database path: {db_path}")
