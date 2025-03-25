import time
from pathlib import Path

import duckdb
import structlog
from catasto.duckdb.repository import DuckDBRepository
from catasto.parser import FileParserService
from catasto.reader import LocalFileReaderService
from catasto.schemas.catastodb.models import Ctfisica, Ctnonfis
from structlog.stdlib import BoundLogger


async def load_soggetti(
    sog_filepath: str,
    duckdb_filepath: str,
    clean_tables: bool,
    logger: BoundLogger = None,
) -> str:
    """
    Carica i dati dei soggetti da un file .Sog in un database DuckDB.

    Args:
        sog_filepath: Percorso al file .Sog
        duckdb_filepath: Percorso al file DuckDB
        clean_tables: Se True, cancella i dati esistenti nelle tabelle
        logger: Logger strutturato da utilizzare (se None, ne viene creato uno)

    Returns:
        str: Percorso al database DuckDB
    """
    # Crea un logger predefinito se non fornito
    if logger is None:
        logger = structlog.get_logger("catasto.duckdb.subject")
    start_time = time.time()
    logger.info(
        "load_started",
        input_file=sog_filepath,
        database=duckdb_filepath,
        clean_tables=clean_tables,
    )

    # Verifiche preliminari
    file_path = Path(sog_filepath)
    db_path = Path(duckdb_filepath)

    if not file_path.exists():
        logger.error(f"File {sog_filepath} non trovato")
        raise FileNotFoundError(f"File {sog_filepath} non trovato.")

    if db_path.exists():
        logger.error(f"File {duckdb_filepath} già esistente")

    # Crea una connessione diretta a DuckDB per inizializzare il database
    logger.debug(f"Connessione al database DuckDB {duckdb_filepath}")
    duck_conn = duckdb.connect(duckdb_filepath)

    try:
        # Crea lo schema se non esiste
        logger.debug("Creazione dello schema ctcn")
        duck_conn.execute("CREATE SCHEMA IF NOT EXISTS ctcn")

        # Crea tutte le tabelle direttamente in DuckDB
        logger.debug("Creazione della tabella ctfisica")
        duck_conn.execute("""
        CREATE TABLE IF NOT EXISTS ctcn.ctfisica (
            codice varchar(4) NOT NULL,
            sezione varchar(1) NOT NULL,
            soggetto int8 NOT NULL,
            tipo_sog varchar(1) NOT NULL,
            cognome varchar(50) NULL,
            nome varchar(50) NULL,
            sesso varchar(1) NULL,
            data varchar(10) NULL,
            luogo varchar(4) NULL,
            codfiscale varchar(16) NULL,
            supplement varchar(100) NULL,
            PRIMARY KEY (codice, sezione, soggetto, tipo_sog)
        )
        """)

        logger.debug("Creazione della tabella ctnonfis")
        duck_conn.execute("""
        CREATE TABLE IF NOT EXISTS ctcn.ctnonfis (
            codice varchar(4) NOT NULL,
            sezione varchar(1) NOT NULL,
            soggetto int8 NOT NULL,
            tipo_sog varchar(1) NOT NULL,
            denominaz varchar(150) NULL,
            sede varchar(4) NULL,
            codfiscale varchar(11) NULL,
            PRIMARY KEY (codice, sezione, soggetto, tipo_sog)
        )
        """)

        # Se richiesto, pulisci le tabelle
        if clean_tables:
            logger.info("Pulizia delle tabelle richiesta")
            for table in ["ctfisica", "ctnonfis"]:
                duck_conn.execute(f"DELETE FROM ctcn.{table}")
            logger.info("Tabelle svuotate con successo")

        # Crea repository manuali senza dipendere dal DAL
        logger.debug("Inizializzazione dei repository")
        ctfisica_repo = DuckDBRepository(
            connection=duck_conn,
            entity_type=Ctfisica,
            table_name="ctcn.ctfisica",
            primary_keys=["codice", "sezione", "soggetto", "tipo_sog"],
        )

        ctnonfis_repo = DuckDBRepository(
            connection=duck_conn,
            entity_type=Ctnonfis,
            table_name="ctcn.ctnonfis",
            primary_keys=["codice", "sezione", "soggetto", "tipo_sog"],
        )

        # Verifica quanti record ci sono nelle tabelle
        count_before = duck_conn.execute(
            "SELECT COUNT(*) FROM ctcn.ctfisica"
        ).fetchone()[0]
        logger.info(
            f"Record esistenti nella tabella ctfisica prima dell'inserimento: {count_before}"
        )

        # Recupera tutti i dati dal file
        logger.info(f"Parsing del file {sog_filepath}")
        reader = LocalFileReaderService(filepath=sog_filepath)
        parser = FileParserService(reader=reader)
        content = await parser.parse()
        breakpoint()
        logger.debug(
            f"Parsing completato, numero di soggetti: {len(content.soggetti.soggetti)}"
        )

        # Processo di elaborazione
        async def process_soggetti():
            # Raccogli tutti i record
            ctfisica_records = []
            ctnonfis_records = []

            if content.soggetti.soggetti:
                logger.debug(
                    f"Elaborazione di {len(content.soggetti.soggetti)} soggetti"
                )
                for soggetto in content.soggetti.soggetti:
                    record = soggetto.record

                    if soggetto.tipo_soggetto == "P":
                        ctfisica_records.append(
                            Ctfisica.extract_from_model(dati_soggetto=record)
                        )
                    elif soggetto.tipo_soggetto == "G":
                        ctnonfis_records.append(
                            Ctnonfis.extract_from_model(dati_soggetto=record)
                        )
                    else:
                        raise ValueError(
                            f"Tipo soggetto {soggetto.tipo_soggetto} non previsto"
                        )

            logger.info(
                f"Record estratti: ctfisica={len(ctfisica_records)}, ctnonfis={len(ctnonfis_records)}"
            )

            # Inserisci tutti i record
            total_records = 0

            insert_start_time = time.time()
            if ctfisica_records:
                logger.info(
                    f"Inserimento di {len(ctfisica_records)} record in ctfisica"
                )
                count = await ctfisica_repo.insert_many(ctfisica_records)
                logger.info(f"Inseriti {count} record in ctfisica")
                total_records += count

            if ctnonfis_records:
                logger.info(
                    f"Inserimento di {len(ctnonfis_records)} record in ctnonfis"
                )
                count = await ctnonfis_repo.insert_many(ctnonfis_records)
                logger.info(f"Inseriti {count} record in ctnonfis")
                total_records += count

            insert_duration = time.time() - insert_start_time
            logger.info(f"Inserimento completato in {insert_duration:.2f} secondi")
            return total_records

        # Esegui il processo
        result = await process_soggetti()
        logger.info(f"Inseriti in totale {result} record")

        # Verifica i dati inseriti
        tables = ["ctfisica", "ctnonfis"]
        for table in tables:
            count = duck_conn.execute(f"SELECT COUNT(*) FROM ctcn.{table}").fetchone()[
                0
            ]
            logger.info(f"Totale record in {table}: {count}")

        # Mostra alcuni esempi (solo nel log di livello debug)
        logger.debug("Esempi di dati in ctfisica:")
        sample = duck_conn.execute("SELECT * FROM ctcn.ctfisica LIMIT 3").fetchall()
        for idx, row in enumerate(sample):
            logger.debug(f"Row {idx+1}: {row}")

        duration = time.time() - start_time
        logger.info(f"Caricamento dati completato in {duration:.2f} secondi")
        return duckdb_filepath

    except Exception as e:
        logger.exception(f"Errore durante il caricamento: {str(e)}")
        raise
    finally:
        # Chiudi la connessione
        logger.debug("Chiusura della connessione al database")
        duck_conn.close()
