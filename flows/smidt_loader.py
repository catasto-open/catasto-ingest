from catasto.postgres.db import DatabaseSynchronizer
from catasto.schemas.catastodb.models import (
    Acque,
    Ctdeduzi,
    Ctfisica,
    Ctnonfis,
    Ctpartic,
    Ctporzio,
    Ctriserv,
    Cttitola,
    Cuarcuiu,
    Cuidenti,
    Cuindiri,
    Curiserv,
    Cuutilit,
    Fabbricati,
    Fogli,
    Particelle,
    Quadri,
    Simboli,
    Strade,
    Testi,
)
from prefect import flow, get_run_logger, task


@task(name="Load Terreni tables to CTCN", log_prints=True, tags="CTCN")
async def sync_terreni_tables(
    source: str,
    dest: str,
):
    logger = get_run_logger()

    # Mappa le tabelle ai tipi di entità
    entity_types = {
        "ctpartic": Ctpartic,
        "ctdeduzi": Ctdeduzi,
        "ctriserv": Ctriserv,
        "ctporzio": Ctporzio,
    }

    # Crea l'istanza del sincronizzatore
    syncer = DatabaseSynchronizer(
        duckdb_path=source,
        pg_conn_string=dest,
        schema="ctcn",
        tables=entity_types.keys(),
    )

    try:
        # Inizializza il sincronizzatore
        await syncer.initialize()

        # Esegui la sincronizzazione
        stats = await syncer.sync_database(entity_types)

        # Stampa le statistiche
        if stats.get("success"):
            logger.info("Sincronizzazione terreni completata:")
            updated = stats["stats"]["updated"]
            inserted = stats["stats"]["inserted"]
            errors = stats["stats"]["errors"]
            logger.info(f"    - Record aggiornati: {updated}")
            logger.info(f"    - Record inseriti: {inserted}")
            logger.info(f"    - Errori: {errors}")

    except Exception as e:
        logger.error(f"Errore durante la sincronizzazione: {str(e)}")
        import traceback

        traceback.print_exc()
    finally:
        # Chiudi le connessioni
        await syncer.close()


@task(name="Load Fabbricati tables to CTCN", log_prints=True, tags="CTCN")
async def sync_fabbricati_tables(
    source: str,
    dest: str,
):
    logger = get_run_logger()

    # Mappa le tabelle ai tipi di entità
    entity_types = {
        "cuarcuiu": Cuarcuiu,
        "cuidenti": Cuidenti,
        "cuindiri": Cuindiri,
        "curiserv": Curiserv,
        "cuutilit": Cuutilit,
    }

    # Crea l'istanza del sincronizzatore
    syncer = DatabaseSynchronizer(
        duckdb_path=source,
        pg_conn_string=dest,
        schema="ctcn",
        tables=entity_types.keys(),
    )

    try:
        # Inizializza il sincronizzatore
        await syncer.initialize()

        # Esegui la sincronizzazione
        stats = await syncer.sync_database(entity_types)

        # Stampa le statistiche
        if stats.get("success"):
            logger.info("Sincronizzazione fabbricati completata:")
            updated = stats["stats"]["updated"]
            inserted = stats["stats"]["inserted"]
            errors = stats["stats"]["errors"]
            logger.info(f"    - Record aggiornati: {updated}")
            logger.info(f"    - Record inseriti: {inserted}")
            logger.info(f"    - Errori: {errors}")

    except Exception as e:
        logger.error(f"Errore durante la sincronizzazione: {str(e)}")
        import traceback

        traceback.print_exc()
    finally:
        # Chiudi le connessioni
        await syncer.close()


@task(name="Load Soggetti tables to CTCN", log_prints=True, tags="CTCN")
async def sync_soggetti_tables(
    source: str,
    dest: str,
):
    logger = get_run_logger()

    # Mappa le tabelle ai tipi di entità
    entity_types = {
        "ctfisica": Ctfisica,
        "ctnonfis": Ctnonfis,
    }

    # Crea l'istanza del sincronizzatore
    syncer = DatabaseSynchronizer(
        duckdb_path=source,
        pg_conn_string=dest,
        schema="ctcn",
        tables=entity_types.keys(),
    )

    try:
        # Inizializza il sincronizzatore
        await syncer.initialize()

        # Esegui la sincronizzazione
        stats = await syncer.sync_database(entity_types)

        # Stampa le statistiche
        if stats.get("success"):
            logger.info("Sincronizzazione soggetti completata:")
            updated = stats["stats"]["updated"]
            inserted = stats["stats"]["inserted"]
            errors = stats["stats"]["errors"]
            logger.info(f"    - Record aggiornati: {updated}")
            logger.info(f"    - Record inseriti: {inserted}")
            logger.info(f"    - Errori: {errors}")

    except Exception as e:
        logger.error(f"Errore durante la sincronizzazione: {str(e)}")
        import traceback

        traceback.print_exc()
    finally:
        # Chiudi le connessioni
        await syncer.close()


@task(name="Load Titolarità tables to CTCN", log_prints=True, tags="CTCN")
async def sync_titolarita_tables(
    source: str,
    dest: str,
):
    logger = get_run_logger()

    # Mappa le tabelle ai tipi di entità
    entity_types = {
        "cttitola": Cttitola,
    }

    # Crea l'istanza del sincronizzatore
    syncer = DatabaseSynchronizer(
        duckdb_path=source,
        pg_conn_string=dest,
        schema="ctcn",
        tables=entity_types.keys(),
    )

    try:
        # Inizializza il sincronizzatore
        await syncer.initialize()

        # Esegui la sincronizzazione
        stats = await syncer.sync_database(entity_types)

        # Stampa le statistiche
        if stats.get("success"):
            logger.info("Sincronizzazione titolarità completata:")
            updated = stats["stats"]["updated"]
            inserted = stats["stats"]["inserted"]
            errors = stats["stats"]["errors"]
            logger.info(f"    - Record aggiornati: {updated}")
            logger.info(f"    - Record inseriti: {inserted}")
            logger.info(f"    - Errori: {errors}")

    except Exception as e:
        logger.error(f"Errore durante la sincronizzazione: {str(e)}")
        import traceback

        traceback.print_exc()
    finally:
        # Chiudi le connessioni
        await syncer.close()


@flow(name="CTCN loading", log_prints=True)
def ctcn_sync_flow(source_db: str = "/tmp/catasto.duckdb", target_db: str = None):
    logger = get_run_logger()

    logger.info("Sincronizzazione dei terreni")
    sync_terreni_tables(source=source_db, dest=target_db)

    logger.info("Sincronizzazione dei fabbricati")
    sync_fabbricati_tables(source=source_db, dest=target_db)

    logger.info("Sincronizzazione dei soggetti")
    sync_soggetti_tables(source=source_db, dest=target_db)

    logger.info("Sincronizzazione delle titolarità")
    sync_titolarita_tables(source=source_db, dest=target_db)


@task(name="Load Cartografico tables to CTMP", log_prints=True, tags="CTMP")
async def sync_carto_tables(
    source: str,
    dest: str,
):
    logger = get_run_logger()

    # Mappa le tabelle ai tipi di entità
    entity_types = {
        "acque": Acque,
        "fabbricati": Fabbricati,
        "fogli": Fogli,
        "particelle": Particelle,
        "quadri": Quadri,
        "simboli": Simboli,
        "strade": Strade,
        "testi": Testi,
    }

    # Crea l'istanza del sincronizzatore
    syncer = DatabaseSynchronizer(
        duckdb_path=source,
        pg_conn_string=dest,
        schema="ctmp",
        tables=entity_types.keys(),
    )

    try:
        # Inizializza il sincronizzatore
        await syncer.initialize()

        # Esegui la sincronizzazione
        stats = await syncer.sync_database(entity_types)

        # Stampa le statistiche
        if stats.get("success"):
            logger.info("Sincronizzazione cartografico completata:")
            updated = stats["stats"]["updated"]
            inserted = stats["stats"]["inserted"]
            errors = stats["stats"]["errors"]
            logger.info(f"    - Record aggiornati: {updated}")
            logger.info(f"    - Record inseriti: {inserted}")
            logger.info(f"    - Errori: {errors}")

    except Exception as e:
        logger.error(f"Errore durante la sincronizzazione: {str(e)}")
        import traceback

        traceback.print_exc()
    finally:
        # Chiudi le connessioni
        await syncer.close()


@flow(name="CTMP loading", log_prints=True)
def ctmp_sync_flow(source_db: str = "/tmp/catasto.duckdb", target_db: str = None):
    logger = get_run_logger()

    logger.info("Sincronizzazione del cartografico")
    sync_carto_tables(source=source_db, dest=target_db)
