import time
from pathlib import Path

import duckdb
import structlog
from structlog.stdlib import BoundLogger

from catasto.duckdb.repository import DuckDBRepository
from catasto.parser import FileParserService
from catasto.reader import LocalFileReaderService
from catasto.schemas.catastodb.models import Ctdeduzi, Ctpartic, Ctporzio, Ctriserv


async def load_terreni(
    ter_filepath: str, duckdb_filepath: str, clean_db: bool, logger: BoundLogger = None
) -> str:
    """
    Carica i dati dei terreni da un file .Ter in un database DuckDB.

    Args:
        ter_filepath: Percorso al file .Ter
        duckdb_filepath: Percorso al file DuckDB
        clean_db: Se True, cancella i dati esistenti nelle tabelle
        logger: Logger strutturato da utilizzare (se None, ne viene creato uno)

    Returns:
        str: Percorso al database DuckDB
    """
    # Crea un logger predefinito se non fornito
    if logger is None:
        logger = structlog.get_logger("catasto.duckdb.land")
    start_time = time.time()
    logger.info(
        "load_started",
        input_file=ter_filepath,
        database=duckdb_filepath,
        clean_db=clean_db,
    )

    # Verifiche preliminari
    file_path = Path(ter_filepath)
    db_path = Path(duckdb_filepath)

    if not file_path.exists():
        logger.error(f"File {ter_filepath} non trovato")
        raise FileNotFoundError(f"File {ter_filepath} non trovato.")

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
        logger.debug("Creazione della tabella ctpartic")
        duck_conn.execute("""
        CREATE TABLE IF NOT EXISTS ctcn.ctpartic (
            codice varchar(4) NOT NULL,
            sezione varchar(1) NOT NULL,
            immobile int8 NOT NULL,
            tipo_imm varchar(1) NOT NULL,
            progressiv int4 NOT NULL,
            foglio int4 NULL,
            numero varchar(5) NULL,
            denominato int4 NULL,
            subalterno varchar(4) NULL,
            edificiale varchar(1) NULL,
            qualita int4 NULL,
            classe varchar(2) NULL,
            ettari int4 NULL,
            are int4 NULL,
            centiare int4 NULL,
            flag_redd varchar(1) NULL,
            flag_porz varchar(1) NULL,
            flag_deduz varchar(1) NULL,
            dominic_l varchar(9) NULL,
            agrario_l varchar(8) NULL,
            dominic_e varchar(12) NULL,
            agrario_e varchar(11) NULL,
            gen_eff varchar(10) NULL,
            gen_regist varchar(10) NULL,
            gen_tipo varchar(1) NULL,
            gen_numero varchar(6) NULL,
            gen_progre varchar(3) NULL,
            gen_anno int4 NULL,
            con_eff varchar(10) NULL,
            con_regist varchar(10) NULL,
            con_tipo varchar(1) NULL,
            con_numero varchar(6) NULL,
            con_progre varchar(3) NULL,
            con_anno int4 NULL,
            partita varchar(7) NULL,
            annotazion varchar(200) NULL,
            mutaz_iniz int4 NULL,
            mutaz_fine int4 NULL,
            gen_causa varchar(3) NULL,
            gen_descr varchar(100) NULL,
            con_causa varchar(3) NULL,
            con_descr varchar(100) NULL,
            PRIMARY KEY (codice, sezione, immobile, tipo_imm, progressiv)
        )
        """)

        logger.debug("Creazione della tabella ctdeduzi")
        duck_conn.execute("""
        CREATE TABLE IF NOT EXISTS ctcn.ctdeduzi (
            codice varchar(4) NOT NULL,
            sezione varchar(1) NOT NULL,
            immobile int8 NOT NULL,
            tipo_imm varchar(1) NOT NULL,
            progressiv int4 NOT NULL,
            deduzione varchar(6) NULL
        )
        """)

        logger.debug("Creazione della tabella ctriserv")
        duck_conn.execute("""
        CREATE TABLE IF NOT EXISTS ctcn.ctriserv (
            codice varchar(4) NOT NULL,
            sezione varchar(1) NOT NULL,
            immobile int8 NOT NULL,
            tipo_imm varchar(1) NOT NULL,
            progressiv int4 NOT NULL,
            riserva varchar(1) NULL,
            iscrizione varchar(7) NULL
        )
        """)

        logger.debug("Creazione della tabella ctporzio")
        duck_conn.execute("""
        CREATE TABLE IF NOT EXISTS ctcn.ctporzio (
            codice varchar(4) NOT NULL,
            sezione varchar(1) NOT NULL,
            immobile int8 NOT NULL,
            tipo_imm varchar(1) NOT NULL,
            progressiv int4 NOT NULL,
            porzione varchar(2) NULL,
            qualita int4 NULL,
            classe varchar(2) NULL,
            ettari int4 NULL,
            are int4 NULL,
            centiare int4 NULL,
            dominic_e varchar(12) NULL,
            agrario_e varchar(11) NULL
        )
        """)

        # Se richiesto, pulisci le tabelle
        if clean_db:
            logger.info("Pulizia delle tabelle richiesta")
            for table in ["ctpartic", "ctdeduzi", "ctriserv", "ctporzio"]:
                duck_conn.execute(f"DELETE FROM ctcn.{table}")
            logger.info("Tabelle svuotate con successo")

        # Crea repository manuali senza dipendere dal DAL
        logger.debug("Inizializzazione dei repository")
        ctpartic_repo = DuckDBRepository(
            connection=duck_conn,
            entity_type=Ctpartic,
            table_name="ctcn.ctpartic",
            primary_keys=["codice", "sezione", "immobile", "tipo_imm", "progressiv"],
        )

        ctdeduzi_repo = DuckDBRepository(
            connection=duck_conn,
            entity_type=Ctdeduzi,
            table_name="ctcn.ctdeduzi",
            primary_keys=["codice", "sezione", "immobile", "tipo_imm", "progressiv"],
        )

        ctriserv_repo = DuckDBRepository(
            connection=duck_conn,
            entity_type=Ctriserv,
            table_name="ctcn.ctriserv",
            primary_keys=["codice", "sezione", "immobile", "tipo_imm", "progressiv"],
        )

        ctporzio_repo = DuckDBRepository(
            connection=duck_conn,
            entity_type=Ctporzio,
            table_name="ctcn.ctporzio",
            primary_keys=["codice", "sezione", "immobile", "tipo_imm", "progressiv"],
        )

        # Verifica quanti record ci sono nelle tabelle
        count_before = duck_conn.execute(
            "SELECT COUNT(*) FROM ctcn.ctpartic"
        ).fetchone()[0]
        logger.info(
            f"Record esistenti nella tabella ctpartic prima dell'inserimento: {count_before}"
        )

        # Recupera tutti i dati dal file
        logger.info(f"Parsing del file {ter_filepath}")
        reader = LocalFileReaderService(filepath=ter_filepath)
        parser = FileParserService(reader=reader)
        content = await parser.parse()
        logger.debug(
            f"Parsing completato, numero di immobili: {len(content.terreni.immobili)}"
        )

        # Processo di elaborazione
        async def process_immobili():
            # Raccogli tutti i record
            ctpartic_records = []
            ctdeduzi_records = []
            ctriserv_records = []
            ctporzio_records = []

            if content.terreni.immobili:
                logger.debug(
                    f"Elaborazione di {len(content.terreni.immobili)} immobili"
                )
                for immobile in content.terreni.immobili:
                    record1 = immobile.record1
                    ctpartic_records.append(
                        Ctpartic.extract_from_model(dati_terreno=record1)
                    )

                    if immobile.record2:
                        for deduzione in immobile.record2.deduzioni:
                            ctdeduzi_records.append(
                                Ctdeduzi.extract_from_model(
                                    dati_terreno=immobile.record2,
                                    dati_deduzione=deduzione,
                                )
                            )

                    if immobile.record3:
                        for riserva in immobile.record3.riserve:
                            ctriserv_records.append(
                                Ctriserv.extract_from_model(
                                    dati_terreno=immobile.record3,
                                    dati_riserva=riserva,
                                )
                            )

                    if immobile.record4:
                        for porzione in immobile.record4.porzioni:
                            ctporzio_records.append(
                                Ctporzio.extract_from_model(
                                    dati_terreno=immobile.record4,
                                    dati_porzione=porzione,
                                )
                            )

            logger.info(
                f"Record estratti: ctpartic={len(ctpartic_records)}, ctdeduzi={len(ctdeduzi_records)}, "
                f"ctriserv={len(ctriserv_records)}, ctporzio={len(ctporzio_records)}, "
            )

            # Inserisci tutti i record
            total_records = 0

            insert_start_time = time.time()
            if ctpartic_records:
                logger.info(
                    f"Inserimento di {len(ctpartic_records)} record in ctpartic"
                )
                count = await ctpartic_repo.insert_many(ctpartic_records)
                logger.info(f"Inseriti {count} record in ctpartic")
                total_records += count

            if ctdeduzi_records:
                logger.info(
                    f"Inserimento di {len(ctdeduzi_records)} record in ctdeduzi"
                )
                count = await ctdeduzi_repo.insert_many(ctdeduzi_records)
                logger.info(f"Inseriti {count} record in ctdeduzi")
                total_records += count

            if ctriserv_records:
                logger.info(
                    f"Inserimento di {len(ctriserv_records)} record in ctriserv"
                )
                count = await ctriserv_repo.insert_many(ctriserv_records)
                logger.info(f"Inseriti {count} record in ctriserv")
                total_records += count

            if ctporzio_records:
                logger.info(
                    f"Inserimento di {len(ctporzio_records)} record in ctporzio"
                )
                count = await ctporzio_repo.insert_many(ctporzio_records)
                logger.info(f"Inseriti {count} record in ctporzio")
                total_records += count

            insert_duration = time.time() - insert_start_time
            logger.info(f"Inserimento completato in {insert_duration:.2f} secondi")
            return total_records

        # Esegui il processo
        result = await process_immobili()
        logger.info(f"Inseriti in totale {result} record")

        # Verifica i dati inseriti
        tables = ["ctpartic", "ctdeduzi", "ctriserv", "ctporzio"]
        for table in tables:
            count = duck_conn.execute(f"SELECT COUNT(*) FROM ctcn.{table}").fetchone()[
                0
            ]
            logger.info(f"Totale record in {table}: {count}")

        # Mostra alcuni esempi (solo nel log di livello debug)
        logger.debug("Esempi di dati in ctpartic:")
        sample = duck_conn.execute("SELECT * FROM ctcn.ctpartic LIMIT 3").fetchall()
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
