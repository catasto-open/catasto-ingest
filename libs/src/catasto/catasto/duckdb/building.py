import time
from pathlib import Path

import duckdb
import structlog
from structlog.stdlib import BoundLogger

from catasto.duckdb.repository import DuckDBRepository
from catasto.parser import FileParserService
from catasto.reader import LocalFileReaderService
from catasto.schemas.catastodb.models import (
    Cuarcuiu,
    Cuidenti,
    Cuindiri,
    Curiserv,
    Cuutilit,
)


async def load_fabbricati(
    fab_filepath: str,
    duckdb_filepath: str,
    clean_tables: bool,
    logger: BoundLogger = None,
) -> str:
    """
    Carica i dati dei fabbricati da un file .Fab in un database DuckDB.

    Args:
        fab_filepath: Percorso al file .Fab
        duckdb_filepath: Percorso al file DuckDB
        clean_tables: Se True, cancella i dati esistenti nelle tabelle
        logger: Logger strutturato da utilizzare (se None, ne viene creato uno)

    Returns:
        str: Percorso al database DuckDB
    """
    # Crea un logger predefinito se non fornito
    if logger is None:
        logger = structlog.get_logger("catasto.duckdb.building")
    start_time = time.time()
    logger.info(
        "load_started",
        input_file=fab_filepath,
        database=duckdb_filepath,
        clean_tables=clean_tables,
    )

    # Verifiche preliminari
    file_path = Path(fab_filepath)
    db_path = Path(duckdb_filepath)

    if not file_path.exists():
        logger.error(f"File {fab_filepath} non trovato")
        raise FileNotFoundError(f"File {fab_filepath} non trovato.")

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
        logger.debug("Creazione della tabella cuarcuiu")
        duck_conn.execute("""
        CREATE TABLE IF NOT EXISTS ctcn.cuarcuiu (
            codice varchar(4) NOT NULL,
            sezione varchar(1) NOT NULL,
            immobile int8 NOT NULL,
            tipo_imm varchar(1) NOT NULL,
            progressiv int4 NOT NULL,
            zona varchar(3) NULL,
            categoria varchar(3) NULL,
            classe varchar(2) NULL,
            consistenz varchar(7) NULL,
            superficie varchar(5) NULL,
            rendita_l varchar(15) NULL,
            rendita_e varchar(18) NULL,
            lotto varchar(2) NULL,
            edificio varchar(2) NULL,
            scala varchar(2) NULL,
            interno_1 varchar(3) NULL,
            interno_2 varchar(3) NULL,
            piano_1 varchar(4) NULL,
            piano_2 varchar(4) NULL,
            piano_3 varchar(4) NULL,
            piano_4 varchar(4) NULL,
            gen_eff varchar(10) NULL,
            gen_regist varchar(10) NULL,
            gen_tipo varchar(1) NULL,
            gen_numero varchar(6) NULL,
            gen_progre varchar(3) NULL,
            gen_anno varchar(4) NULL,
            con_eff varchar(10) NULL,
            con_regist varchar(10) NULL,
            con_tipo varchar(1) NULL,
            con_numero varchar(6) NULL,
            con_progre varchar(3) NULL,
            con_anno varchar(4) NULL,
            partita varchar(7) NULL,
            annotazion varchar(200) NULL,
            mutaz_iniz int4 NULL,
            mutaz_fine int4 NULL,
            prot_notif varchar(18) NULL,
            data_notif varchar(8) NULL,
            gen_causa varchar(3) NULL,
            gen_descr varchar(100) NULL,
            con_causa varchar(3) NULL,
            con_descr varchar(100) NULL,
            flag_class varchar(1) NULL,
            PRIMARY KEY (codice, sezione, immobile, tipo_imm, progressiv)
        )
        """)

        logger.debug("Creazione della tabella cuidenti")
        duck_conn.execute("""
        CREATE TABLE IF NOT EXISTS ctcn.cuidenti (
            codice varchar(4) NOT NULL,
            sezione varchar(1) NOT NULL,
            immobile int8 NOT NULL,
            tipo_imm varchar(1) NOT NULL,
            progressiv int4 NOT NULL,
            sez_urbana varchar(3) NULL,
            foglio varchar(4) NULL,
            numero varchar(5) NULL,
            denominato int4 NULL,
            subalterno varchar(4) NULL,
            edificiale varchar(1) NULL
        )
        """)

        logger.debug("Creazione della tabella cuindiri")
        duck_conn.execute("""
        CREATE TABLE IF NOT EXISTS ctcn.cuindiri (
            codice varchar(4) NOT NULL,
            sezione varchar(1) NOT NULL,
            immobile int8 NOT NULL,
            tipo_imm varchar(1) NOT NULL,
            progressiv int4 NOT NULL,
            toponimo int4 NULL,
            indirizzo varchar(50) NULL,
            civico1 varchar(6) NULL,
            civico2 varchar(6) NULL,
            civico3 varchar(6) NULL,
            cod_strada varchar(5) NULL
        )
        """)

        logger.debug("Creazione della tabella cuutilit")
        duck_conn.execute("""
        CREATE TABLE IF NOT EXISTS ctcn.cuutilit (
            codice varchar(4) NOT NULL,
            sezione varchar(1) NOT NULL,
            immobile int8 NOT NULL,
            tipo_imm varchar(1) NOT NULL,
            progressiv int4 NOT NULL,
            sez_urbana varchar(3) NULL,
            foglio varchar(4) NULL,
            numero varchar(5) NULL,
            denominato int4 NULL,
            subalterno varchar(4) NULL
        )
        """)

        logger.debug("Creazione della tabella curiserv")
        duck_conn.execute("""
        CREATE TABLE IF NOT EXISTS ctcn.curiserv (
            codice varchar(4) NOT NULL,
            sezione varchar(1) NOT NULL,
            immobile int8 NOT NULL,
            tipo_imm varchar(1) NOT NULL,
            progressiv int4 NOT NULL,
            riserva varchar(1) NULL,
            iscrizione varchar(7) NULL
        )
        """)

        # Se richiesto, pulisci le tabelle
        if clean_tables:
            logger.info("Pulizia delle tabelle richiesta")
            for table in ["cuarcuiu", "cuidenti", "cuindiri", "cuutilit", "curiserv"]:
                duck_conn.execute(f"DELETE FROM ctcn.{table}")
            logger.info("Tabelle svuotate con successo")

        # Crea repository manuali senza dipendere dal DAL
        logger.debug("Inizializzazione dei repository")
        cuarcuiu_repo = DuckDBRepository(
            connection=duck_conn,
            entity_type=Cuarcuiu,
            table_name="ctcn.cuarcuiu",
            primary_keys=["codice", "sezione", "immobile", "tipo_imm", "progressiv"],
        )

        cuidenti_repo = DuckDBRepository(
            connection=duck_conn,
            entity_type=Cuidenti,
            table_name="ctcn.cuidenti",
            primary_keys=["codice", "sezione", "immobile", "tipo_imm", "progressiv"],
        )

        cuindiri_repo = DuckDBRepository(
            connection=duck_conn,
            entity_type=Cuindiri,
            table_name="ctcn.cuindiri",
            primary_keys=["codice", "sezione", "immobile", "tipo_imm", "progressiv"],
        )

        cuutilit_repo = DuckDBRepository(
            connection=duck_conn,
            entity_type=Cuutilit,
            table_name="ctcn.cuutilit",
            primary_keys=["codice", "sezione", "immobile", "tipo_imm", "progressiv"],
        )

        curiserv_repo = DuckDBRepository(
            connection=duck_conn,
            entity_type=Curiserv,
            table_name="ctcn.curiserv",
            primary_keys=["codice", "sezione", "immobile", "tipo_imm", "progressiv"],
        )

        # Verifica quanti record ci sono nelle tabelle
        count_before = duck_conn.execute(
            "SELECT COUNT(*) FROM ctcn.cuarcuiu"
        ).fetchone()[0]
        logger.info(
            f"Record esistenti nella tabella cuarcuiu prima dell'inserimento: {count_before}"
        )

        # Recupera tutti i dati dal file
        logger.info(f"Parsing del file {fab_filepath}")
        reader = LocalFileReaderService(filepath=fab_filepath)
        parser = FileParserService(reader=reader)
        content = await parser.parse()
        logger.debug(
            f"Parsing completato, numero di immobili: {len(content.fabbricati.immobili)}"
        )

        # Processo di elaborazione
        async def process_immobili():
            # Raccogli tutti i record
            cuarcuiu_records = []
            cuidenti_records = []
            cuindiri_records = []
            cuutilit_records = []
            curiserv_records = []

            if content.fabbricati.immobili:
                logger.debug(
                    f"Elaborazione di {len(content.fabbricati.immobili)} immobili"
                )
                for immobile in content.fabbricati.immobili:
                    record1 = immobile.record1
                    cuarcuiu_records.append(
                        Cuarcuiu.extract_from_model(dati_fabbricato=record1)
                    )

                    if immobile.record2:
                        for identificativo in immobile.record2.identificativi:
                            cuidenti_records.append(
                                Cuidenti.extract_from_model(
                                    dati_fabbricato=immobile.record2,
                                    dati_identificativo=identificativo,
                                )
                            )

                    if immobile.record3:
                        for indirizzo in immobile.record3.indirizzi:
                            cuindiri_records.append(
                                Cuindiri.extract_from_model(
                                    dati_fabbricato=immobile.record3,
                                    dati_indirizzo=indirizzo,
                                )
                            )

                    if immobile.record4:
                        for utilita in immobile.record4.utilita_comuni:
                            cuutilit_records.append(
                                Cuutilit.extract_from_model(
                                    dati_fabbricato=immobile.record4,
                                    dati_utilita=utilita,
                                )
                            )

                    if immobile.record5:
                        for riserva in immobile.record5.riserve:
                            curiserv_records.append(
                                Curiserv.extract_from_model(
                                    dati_fabbricato=immobile.record5,
                                    dati_riserva=riserva,
                                )
                            )

            logger.info(
                f"Record estratti: cuarcuiu={len(cuarcuiu_records)}, cuidenti={len(cuidenti_records)}, "
                f"cuindiri={len(cuindiri_records)}, cuutilit={len(cuutilit_records)}, "
                f"curiserv={len(curiserv_records)}"
            )

            # Inserisci tutti i record
            total_records = 0

            insert_start_time = time.time()
            if cuarcuiu_records:
                logger.info(
                    f"Inserimento di {len(cuarcuiu_records)} record in cuarcuiu"
                )
                count = await cuarcuiu_repo.insert_many(cuarcuiu_records)
                logger.info(f"Inseriti {count} record in cuarcuiu")
                total_records += count

            if cuidenti_records:
                logger.info(
                    f"Inserimento di {len(cuidenti_records)} record in cuidenti"
                )
                count = await cuidenti_repo.insert_many(cuidenti_records)
                logger.info(f"Inseriti {count} record in cuidenti")
                total_records += count

            if cuindiri_records:
                logger.info(
                    f"Inserimento di {len(cuindiri_records)} record in cuindiri"
                )
                count = await cuindiri_repo.insert_many(cuindiri_records)
                logger.info(f"Inseriti {count} record in cuindiri")
                total_records += count

            if cuutilit_records:
                logger.info(
                    f"Inserimento di {len(cuutilit_records)} record in cuutilit"
                )
                count = await cuutilit_repo.insert_many(cuutilit_records)
                logger.info(f"Inseriti {count} record in cuutilit")
                total_records += count

            if curiserv_records:
                logger.info(
                    f"Inserimento di {len(curiserv_records)} record in curiserv"
                )
                count = await curiserv_repo.insert_many(curiserv_records)
                logger.info(f"Inseriti {count} record in curiserv")
                total_records += count

            insert_duration = time.time() - insert_start_time
            logger.info(f"Inserimento completato in {insert_duration:.2f} secondi")
            return total_records

        # Esegui il processo
        result = await process_immobili()
        logger.info(f"Inseriti in totale {result} record")

        # Verifica i dati inseriti
        tables = ["cuarcuiu", "cuidenti", "cuindiri", "cuutilit", "curiserv"]
        for table in tables:
            count = duck_conn.execute(f"SELECT COUNT(*) FROM ctcn.{table}").fetchone()[
                0
            ]
            logger.info(f"Totale record in {table}: {count}")

        # Mostra alcuni esempi (solo nel log di livello debug)
        logger.debug("Esempi di dati in cuarcuiu:")
        sample = duck_conn.execute("SELECT * FROM ctcn.cuarcuiu LIMIT 3").fetchall()
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
