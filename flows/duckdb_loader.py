import asyncio
from pathlib import Path

from catasto.duckdb.building import load_fabbricati
from catasto.duckdb.land import load_terreni
from prefect import flow, get_run_logger, task


@task(name="Load FAB file to CTCN", log_prints=True, tags="CTCN")
def load_fab_file(
    fab_filepath: str,
    duckdb_filepath: str,
    clean_tables: bool,
):
    db_path = asyncio.run(
        load_fabbricati(
            fab_filepath=fab_filepath,
            duckdb_filepath=duckdb_filepath,
            clean_tables=clean_tables,
        )
    )
    return db_path


@task(name="Load TER file to CTCN", log_prints=True, tags="CTCN")
def load_ter_file(
    ter_filepath: str,
    duckdb_filepath: str,
    clean_tables: bool,
):
    db_path = asyncio.run(
        load_terreni(
            ter_filepath=ter_filepath,
            duckdb_filepath=duckdb_filepath,
            clean_tables=clean_tables,
        )
    )
    return db_path


@task(name="Load SOG file to CTCN", log_prints=True, tags="CTCN")
def load_sog_file(
    sog_filepath: str,
    duckdb_filepath: str,
    clean_tables: bool,
):
    pass


@task(name="Load TIT file to CTCN", log_prints=True, tags="CTCN")
def load_tit_file(
    tit_filepath: str,
    duckdb_filepath: str,
    clean_tables: bool,
):
    pass


@flow(name="CTCN loading", log_prints=True)
def ctcn_flow(
    fab_files: list = None,
    ter_files: list = None,
    sog_files: list = None,
    tit_files: list = None,
    catasto_db: str = "/tmp/catasto.duckdb",
    empty_db: bool = False,
):
    logger = get_run_logger()
    db = Path(catasto_db)

    if empty_db:
        if db.exists():
            db.unlink()
    if fab_files:
        for fab_file in fab_files:
            logger.info(f"Loading FAB file: {fab_file}")
            if db.exists():
                clean_tables = False
            else:
                clean_tables = True
            db = Path(
                load_fab_file(
                    fab_filepath=fab_file,
                    duckdb_filepath=str(db),
                    clean_tables=clean_tables,
                )
            )
    if ter_files:
        for ter_file in ter_files:
            logger.info(f"Loading TER file: {ter_file}")
            if db.exists():
                clean_tables = False
            else:
                clean_tables = True
            db = Path(
                load_ter_file(
                    ter_filepath=ter_file,
                    duckdb_filepath=str(db),
                    clean_tables=clean_tables,
                )
            )
    if sog_files:
        for sog_file in sog_files:
            logger.info(f"Loading SOG file: {sog_file}")
            if db.exists():
                clean_tables = False
            else:
                clean_tables = True
            db = Path(
                load_sog_file(
                    sog_filepath=sog_file,
                    duckdb_filepath=str(db),
                    clean_tables=clean_tables,
                )
            )
    if tit_files:
        for tit_file in tit_files:
            logger.info(f"Loading TIT file: {tit_file}")
            if db.exists():
                clean_tables = False
            else:
                clean_tables = True
            db = Path(
                load_tit_file(
                    tit_filepath=tit_file,
                    duckdb_filepath=str(db),
                    clean_tables=clean_tables,
                )
            )
    return str(db)
