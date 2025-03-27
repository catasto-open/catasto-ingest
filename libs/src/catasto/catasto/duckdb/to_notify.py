import time
from pathlib import Path

import argparse
import logging
import duckdb
import psycopg2
import structlog
from structlog.stdlib import BoundLogger

def load_ids_to_notify_to_ancillary(
    duckdb_filepath: str,
    pg_conn_string: str,
    pg_immobili_di_interesse_query: str,
    clean_tables: bool,
    logger: BoundLogger = None,
) -> str:
    """
    Prepara la tabella con gli identificativi da notificare ad un sistema ancillare.
    Viene lanciato alla fine dei task di aggiornamento.
    Non mandata tutti gli identificativi aggiornati, 
    ma solo quelli restituiti dalla query guida pg_immobili_di_interesse_query fatta verso il db postgres.

    Args:
        duckdb_filepath: Percorso al file DuckDB
        pg_conn_string: Connessione al db postgres con i dati del catasto
        pg_immobili_di_interesse_query: La query che contiene gli identificativi immobile di interesse (codice_comune,codice_immobile,tipo_immobile)
            Es:
                SELECT tit.codice as codice_comune,
                tit.immobile as codice_immobile,
                tit.tipo_imm as tipo_immobile
                FROM ctcn.titolarita_qualcosa tit
                GROUP BY tit.codice, tit.immobile, tit.tipo_imm;
        clean_tables: Se True (raccomandato se i contenuti passati sono già inviati alle code), cancella i dati esistenti nella tabella to_notify_ancillary
        logger: Logger strutturato da utilizzare (se None, ne viene creato uno)

    Returns:
        str: Percorso al database DuckDB
    """
    # Crea un logger predefinito se non fornito
    if logger is None:
        logger = structlog.get_logger("catasto.duckdb.to_notify")
    start_time = time.time()
    logger.info(
        "load_started",
        pg_conn_string=pg_conn_string,
        database=duckdb_filepath,
        clean_tables=clean_tables,
        pg_immobili_di_interesse_query=pg_immobili_di_interesse_query 
    )

    # Verifiche preliminari
    db_path = Path(duckdb_filepath)

    if db_path.exists():
        logger.info(f"File {duckdb_filepath} già esistente")
    else:
        logger.error(f"File {duckdb_filepath} non trovato")
        raise FileNotFoundError(f"File {duckdb_filepath} non trovato")

    # Crea una connessione diretta a DuckDB per inizializzare il database
    logger.debug(f"Connessione al database DuckDB {duckdb_filepath}")

    with duckdb.connect(duckdb_filepath) as duck_conn:
        # Crea lo schema se non esiste
        logger.debug("Creazione dello schema ctcn")
        duck_conn.execute("CREATE SCHEMA IF NOT EXISTS ctcn")

        # Crea tutte le tabelle direttamente in DuckDB
        logger.debug("Creazione della tabella to_notify_ancillary")
        duck_conn.execute("""
        CREATE TABLE IF NOT EXISTS ctcn.to_notify_ancillary (
            codice_immobile int8 NOT NULL,
            tipo_immobile varchar(1) NOT NULL,
            data_modifica varchar(10) NOT NULL,
            tipo_operazione varchar(32),
            PRIMARY KEY (codice_immobile, tipo_immobile, data_modifica)
        )
        """)

        # Se richiesto, pulisci la tabella
        if clean_tables:
            logger.info("Pulizia della tabella richiesta")
            duck_conn.execute(f"DELETE FROM ctcn.to_notify_ancillary")
            logger.info("Tabella svuotata con successo")

        # Check PostgreSQL connection
        try:
            logger.debug("Testing PostgreSQL connection")
            with psycopg2.connect(pg_conn_string) as pg_conn:
                logger.info("PostgreSQL connection successful")
        except Exception as e:
            logger.error(f"PostgreSQL connection error: {e}")
            raise

        # Create DuckDB table ctcn.immobili_di_interesse
        duck_conn.execute("""
        CREATE TABLE IF NOT EXISTS ctcn.immobili_di_interesse (
            codice_comune varchar(4),
            codice_immobile int8,
            tipo_immobile varchar(1),
            PRIMARY KEY (codice_comune, codice_immobile, tipo_immobile)
        )
        """)

        # Clean and populate immobili_di_interesse
        logger.debug("Populating immobili_di_interesse from PostgreSQL")
        with psycopg2.connect(pg_conn_string) as pg_conn:
            with pg_conn.cursor() as cur:
                cur.execute(pg_immobili_di_interesse_query)
                rows = cur.fetchall()

        if clean_tables:
            duck_conn.execute("DELETE FROM ctcn.immobili_di_interesse")

        duck_conn.executemany(
            "INSERT INTO ctcn.immobili_di_interesse VALUES (?, ?, ?)",
            rows
        )
        logger.info(f"Inserted {len(rows)} rows into immobili_di_interesse")

        # Utility function to check existence of DuckDB tables
        def duckdb_table_exists(connection, schema, table):
            query = "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = ? AND table_name = ?"
            result = connection.execute(query, [schema, table]).fetchone()
            return result[0] > 0

        # Insert records into ctcn.to_notify_ancillary from ctcn.ctpartic
        if duckdb_table_exists(duck_conn, 'ctcn', 'ctpartic'):
            duck_conn.execute("""
                INSERT INTO ctcn.to_notify_ancillary (codice_immobile, tipo_immobile, data_modifica, tipo_operazione)
                SELECT DISTINCT immobile, tipo_imm, gen_eff,
                    CASE
                        WHEN gen_causa IN ('FRZ', '033') THEN 'FRAZIONAMENTO'
                        ELSE NULL
                    END
                FROM ctcn.ctpartic
                WHERE (codice, immobile, tipo_imm) IN (
                    SELECT codice_comune, codice_immobile, tipo_immobile FROM ctcn.immobili_di_interesse
                ) AND NOT EXISTS (
                    SELECT 1 FROM ctcn.to_notify_ancillary tnr
                    WHERE tnr.codice_immobile = ctpartic.immobile
                    AND tnr.tipo_immobile = ctpartic.tipo_imm
                    AND tnr.data_modifica = ctpartic.gen_eff
                )
            """)
            logger.info(f"Inserted records from ctpartic")
        else:
            logger.warning(f"The table ctpartic is missing")

        # Insert records from ctcn.cuarcuiu
        if duckdb_table_exists(duck_conn, 'ctcn', 'cuarcuiu'):
            duck_conn.execute("""
                INSERT INTO ctcn.to_notify_ancillary (codice_immobile, tipo_immobile, data_modifica, tipo_operazione)
                SELECT DISTINCT immobile, tipo_imm, gen_eff,
                    CASE
                        WHEN gen_causa IN ('FRZ', 'FRV', 'FRF') THEN 'FRAZIONAMENTO'
                        WHEN gen_causa = 'FUS' THEN 'ACCORPAMENTO'
                        ELSE NULL
                    END
                FROM ctcn.cuarcuiu
                WHERE (codice, immobile, tipo_imm) IN (
                    SELECT codice_comune, codice_immobile, tipo_immobile FROM ctcn.immobili_di_interesse
                ) AND NOT EXISTS (
                    SELECT 1 FROM ctcn.to_notify_ancillary tnr
                    WHERE tnr.codice_immobile = cuarcuiu.immobile
                    AND tnr.tipo_immobile = cuarcuiu.tipo_imm
                    AND tnr.data_modifica = cuarcuiu.gen_eff
                )
            """)
            logger.info(f"Inserted records from cuarcuiu")
        else:
            logger.warning(f"The table cuarcuiu is missing")

        # Insert records from ctcn.cttitola
        if duckdb_table_exists(duck_conn, 'ctcn', 'cttitola'):
            duck_conn.execute("""
                INSERT INTO ctcn.to_notify_ancillary (codice_immobile, tipo_immobile, data_modifica, tipo_operazione)
                SELECT DISTINCT immobile, tipo_imm, gen_valida, NULL
                FROM ctcn.cttitola
                WHERE (codice, immobile, tipo_imm) IN (
                    SELECT codice_comune, codice_immobile, tipo_immobile FROM ctcn.immobili_di_interesse
                ) AND NOT EXISTS (
                    SELECT 1 FROM ctcn.to_notify_ancillary tnr
                    WHERE tnr.codice_immobile = cttitola.immobile
                    AND tnr.tipo_immobile = cttitola.tipo_imm
                    AND tnr.data_modifica = cttitola.gen_valida
                )
            """)
            logger.info(f"Inserted records from cttitola")
        else:
            logger.warning(f"The table cttitola is missing")

        # Final report
        final_count = duck_conn.execute("SELECT COUNT(*) FROM ctcn.to_notify_ancillary").fetchone()[0]
        logger.info(f"Total records in to_notify_ancillary: {final_count}")

        duration = time.time() - start_time
        logger.info("load_completed", duration=duration)

        return duckdb_filepath

def main():
    parser = argparse.ArgumentParser(description="Test loader function")

    parser.add_argument("--duckdb_filepath", default="/tmp/catasto.duckdb", help="Percorso file DuckDB")
    parser.add_argument("--pg_conn_string", default="postgresql://siscatsrv:siscatsrv@localhost:5433/siscat", help="Connessione PostgreSQL")
    parser.add_argument("--pg_immobili_di_interesse_query", default="SELECT tit.codice as codice_comune, tit.immobile as codice_immobile, tit.tipo_imm as tipo_immobile FROM ctcn.titolarita_big_city tit GROUP BY tit.codice, tit.immobile, tit.tipo_imm", help="Query immobili di interesse")

    args = parser.parse_args()

    logger = structlog.get_logger("main_test")

    try:
        result = load_ids_to_notify_to_ancillary(
            duckdb_filepath=args.duckdb_filepath,
            pg_conn_string=args.pg_conn_string,
            pg_immobili_di_interesse_query=args.pg_immobili_di_interesse_query,
            clean_tables=True,
            logger=logger
        )
        logger.info(f"Loader completato con successo. Risultato: {result}")

        # Debug print of the first 20 rows from ctcn.to_notify_ancillary
        with duckdb.connect(args.duckdb_filepath) as duck_conn:
            rows = duck_conn.execute(
                "SELECT * FROM ctcn.to_notify_ancillary LIMIT 20"
            ).fetchall()

            print("\nPrimi 20 record in ctcn.to_notify_ancillary:")
            for row in rows:
                print(row)

    except Exception as e:
        logger.exception("Errore durante il caricamento dati", exc_info=e)

if __name__ == "__main__":
    main()