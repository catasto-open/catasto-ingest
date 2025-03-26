import time
from pathlib import Path

import duckdb
import structlog
from catasto.duckdb.repository import DuckDBRepository
from catasto.parser import FileParserService
from catasto.reader import LocalFileReaderService
from catasto.schemas.catastodb.models import Cttitola
from structlog.stdlib import BoundLogger


async def load_titolarita(
    tit_filepath: str,
    duckdb_filepath: str,
    clean_tables: bool,
    logger: BoundLogger = None,
) -> str:
    """
    Carica i dati dei titolarita da un file .Tit in un database DuckDB.

    Args:
        tit_filepath: Percorso al file .Tit
        duckdb_filepath: Percorso al file DuckDB
        clean_tables: Se True, cancella i dati esistenti nelle tabelle
        logger: Logger strutturato da utilizzare (se None, ne viene creato uno)

    Returns:
        str: Percorso al database DuckDB
    """
    # Crea un logger predefinito se non fornito
    if logger is None:
        logger = structlog.get_logger("catasto.duckdb.entitlement")
    start_time = time.time()
    logger.info(
        "load_started",
        input_file=tit_filepath,
        database=duckdb_filepath,
        clean_tables=clean_tables,
    )

    # Verifiche preliminari
    file_path = Path(tit_filepath)
    db_path = Path(duckdb_filepath)

    if not file_path.exists():
        logger.error(f"File {tit_filepath} non trovato")
        raise FileNotFoundError(f"File {tit_filepath} non trovato.")

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
        logger.debug("Creazione della tabella cttitola")
        duck_conn.execute("""
        CREATE TABLE IF NOT EXISTS ctcn.cttitola (
            codice varchar(4) NOT NULL,
            sezione varchar(1) NOT NULL,
            soggetto int8 NOT NULL,
            tipo_sog varchar(1) NOT NULL,
            immobile int8 NOT NULL,
            tipo_imm varchar(1) NOT NULL,
            diritto varchar(3) NULL,
            titolo varchar(200) NULL,
            numeratore int4 NULL,
            denominato int4 NULL,
            regime varchar(1) NULL,
            rif_regime int4 NULL,
            gen_valida varchar(10) NULL,
            gen_nota varchar(1) NULL,
            gen_numero varchar(6) NULL,
            gen_progre varchar(3) NULL,
            gen_anno varchar(4) NULL,
            gen_regist varchar(10) NULL,
            partita varchar(7) NULL,
            con_valida varchar(10) NULL,
            con_nota varchar(1) NULL,
            con_numero varchar(6) NULL,
            con_progre varchar(3) NULL,
            con_anno varchar(4) NULL,
            con_regist varchar(10) NULL,
            mutaz_iniz int4 NULL,
            mutaz_fine int4 NULL,
            identifica int4 NOT NULL,
            gen_causa varchar(3) NULL,
            gen_descr varchar(100) NULL,
            con_causa varchar(3) NULL,
            con_descr varchar(100) NULL,
            PRIMARY KEY (codice, sezione, identifica)
        )
        """)

        # Se richiesto, pulisci le tabelle
        if clean_tables:
            logger.info("Pulizia delle tabelle richiesta")
            for table in ["cttitola"]:
                duck_conn.execute(f"DELETE FROM ctcn.{table}")
            logger.info("Tabelle svuotate con successo")

        # Crea repository manuali senza dipendere dal DAL
        logger.debug("Inizializzazione dei repository")
        cttitola_repo = DuckDBRepository(
            connection=duck_conn,
            entity_type=Cttitola,
            table_name="ctcn.cttitola",
            primary_keys=[
                "codice",
                "sezione",
                "identifica",
            ],
        )

        # Verifica quanti record ci sono nelle tabelle
        count_before = duck_conn.execute(
            "SELECT COUNT(*) FROM ctcn.cttitola"
        ).fetchone()[0]
        logger.info(
            f"Record esistenti nella tabella cttitola prima dell'inserimento: {count_before}"
        )

        # Recupera tutti i dati dal file
        logger.info(f"Parsing del file {tit_filepath}")
        reader = LocalFileReaderService(filepath=tit_filepath)
        parser = FileParserService(reader=reader)
        content = await parser.parse()
        logger.debug(
            f"Parsing completato, numero di titolarità: {len(content.titolarita.titolarita)}"
        )

        # Processo di elaborazione
        async def process_titolarita():
            # Raccogli tutti i record
            cttitola_records = []

            if content.titolarita.titolarita:
                logger.debug(
                    f"Elaborazione di {len(content.titolarita.titolarita)} titolarità"
                )
                for titolarita in content.titolarita.titolarita:
                    record = titolarita
                    cttitola_records.append(
                        Cttitola.extract_from_model(dati_titolarita=record)
                    )

            logger.info(f"Record estratti: cttitola={len(cttitola_records)}")

            # Inserisci tutti i record
            total_records = 0

            insert_start_time = time.time()
            if cttitola_records:
                logger.info(
                    f"Inserimento di {len(cttitola_records)} record in cttitola"
                )
                count = await cttitola_repo.insert_many(cttitola_records)
                logger.info(f"Inseriti {count} record in cttitola")
                total_records += count

            insert_duration = time.time() - insert_start_time
            logger.info(f"Inserimento completato in {insert_duration:.2f} secondi")
            return total_records

        # Esegui il processo
        result = await process_titolarita()
        logger.info(f"Inseriti in totale {result} record")

        # Verifica i dati inseriti
        tables = ["cttitola"]
        for table in tables:
            count = duck_conn.execute(f"SELECT COUNT(*) FROM ctcn.{table}").fetchone()[
                0
            ]
            logger.info(f"Totale record in {table}: {count}")

        # Mostra alcuni esempi (solo nel log di livello debug)
        logger.debug("Esempi di dati in cttitola:")
        sample = duck_conn.execute("SELECT * FROM ctcn.cttitola LIMIT 3").fetchall()
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
