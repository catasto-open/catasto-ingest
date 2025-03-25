import datetime
import json
import os
from pathlib import Path
from typing import Any, Dict, List
from typing import Tuple as TupleType
from typing import Type

import duckdb
import structlog
from catasto.duckdb.repository import DuckDBRepository
from catasto.duckdb.repository import T as TDDB
from catasto.postgres.dal import PostgresDataAccessLayer
from catasto.postgres.repository import PostgresRepository
from catasto.postgres.repository import T as TPG
from catasto.schemas.catastodb.models import Ctfisica, Ctnonfis
from pydantic import BaseModel
from sqlalchemy import text


# Classe per la sincronizzazione tra DuckDB e PostgreSQL
class DatabaseSynchronizer:
    def __init__(
        self,
        duckdb_path: str,
        pg_conn_string: str,
        schema: str = "ctcn",
        tables: List[str] = None,
        backup_base_dir: str = "/tmp/backups",
    ):
        """
        Inizializza il sincronizzatore tra DuckDB e PostgreSQL.

        Args:
            duckdb_path: Percorso al database DuckDB
            pg_conn_string: Stringa di connessione PostgreSQL
            schema: Schema da sincronizzare
            tables: Tabelle da sincronizzare
            backup_base_dir: Directory di base per i backup
        """
        self.duckdb_path = duckdb_path
        self.pg_conn_string = pg_conn_string
        self.schema = schema
        self.tables = tables
        self.backup_base_dir = backup_base_dir
        self.duck_conn = None
        self.pg_dal = None
        self.stats = {"updated": 0, "inserted": 0, "errors": 0}
        self.logger = structlog.get_logger().bind(component="DatabaseSynchronizer")

        # Attributi per memorizzare i repository
        self.duck_repos = {}
        self.pg_repos = {}

    async def initialize(self):
        """Inizializza le connessioni e i repository."""
        self.logger.info(
            "initializing_synchronizer",
            duckdb_path=self.duckdb_path,
            postgres_schema=self.schema,
            tables=self.tables,
        )

        # Inizializza la connessione DuckDB
        self.duck_conn = duckdb.connect(self.duckdb_path)

        # Installa e carica l'estensione postgres_scanner
        try:
            self.duck_conn.execute("INSTALL postgres_scanner;")
            self.duck_conn.execute("LOAD postgres_scanner;")
        except:
            try:
                self.duck_conn.execute("LOAD postgres_scanner;")
            except Exception as e:
                self.logger.warning("postgres_scanner_not_available", error=str(e))

        # Inizializza il DAL PostgreSQL
        self.pg_dal = PostgresDataAccessLayer(self.pg_conn_string)
        self.pg_dal.connect()

        # Crea la directory di backup se non esiste
        os.makedirs(self.backup_base_dir, exist_ok=True)

    async def close(self):
        """Chiude le connessioni."""
        if self.duck_conn:
            self.duck_conn.close()
            self.duck_conn = None

        if self.pg_dal:
            self.pg_dal.close()
            self.pg_dal = None

    def _get_duck_repository(
        self, entity_type: Type[TDDB], table_name: str
    ) -> DuckDBRepository[TDDB]:
        """Ottiene o crea un repository DuckDB per l'entità specificata."""
        key = f"{self.schema}.{table_name}"

        if key not in self.duck_repos:
            # Ottieni le chiavi primarie
            if entity_type in [Ctfisica, Ctnonfis]:
                primary_keys = [
                    "codice",
                    "sezione",
                    "soggetto",
                    "tipo_sog",
                ]
            else:
                primary_keys = [
                    "codice",
                    "sezione",
                    "immobile",
                    "tipo_imm",
                    "progressiv",
                ]

            # Crea il repository
            self.duck_repos[key] = DuckDBRepository(
                connection=self.duck_conn,
                entity_type=entity_type,
                table_name=f"{self.schema}.{table_name}",
                primary_keys=primary_keys,
            )

        return self.duck_repos[key]

    def _get_pg_repository(
        self, entity_type: Type[TPG], table_name: str
    ) -> PostgresRepository[TPG]:
        """Ottiene o crea un repository PostgreSQL per l'entità specificata."""
        key = f"{self.schema}.{table_name}"

        if key not in self.pg_repos:
            # Crea il repository
            self.pg_repos[key] = PostgresRepository(
                dal=self.pg_dal,
                entity_type=entity_type,
                table_name=table_name,
                schema=self.schema,
            )

        return self.pg_repos[key]

    async def backup_postgres_to_parquet(
        self, timestamp: str = None
    ) -> Dict[str, Dict]:
        """
        Esegue un backup dello stato delle tabelle PostgreSQL in formato Parquet
        utilizzando il driver postgres_scanner di DuckDB.
        """
        logger = self.logger.bind(action="backup_postgres")
        logger.info("starting_postgres_backup")

        # Genera un timestamp se non fornito
        if timestamp is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        # Crea la directory di backup
        backup_dir = os.path.join(self.backup_base_dir, "postgres_backups")
        backup_path = Path(backup_dir) / timestamp
        backup_path.mkdir(parents=True, exist_ok=True)

        # Crea un file di metadati
        metadata = {
            "timestamp": timestamp,
            "schema": self.schema,
            "tables": {},
            "backup_date": datetime.datetime.now().isoformat(),
        }

        for table in self.tables:
            table_logger = logger.bind(table=table)
            table_logger.info("backing_up_table")

            try:
                # Verifica l'esistenza della tabella in PostgreSQL
                verify_query = f"""
                SELECT EXISTS (
                    SELECT FROM postgres_scan(
                        '{self.pg_conn_string}',
                        'SELECT 1 FROM information_schema.tables WHERE table_schema = ''{self.schema}'' AND table_name = ''{table}'''
                    )
                );
                """
                exists = self.duck_conn.execute(verify_query).fetchone()[0]

                if not exists:
                    table_logger.warning("table_not_found_in_postgres")
                    metadata["tables"][table] = {
                        "status": "skipped",
                        "reason": "table_not_found",
                    }
                    continue

                # Ottieni il conteggio totale dei record
                count_query = f"""
                SELECT COUNT(*) FROM postgres_scan(
                    '{self.pg_conn_string}',
                    '{self.schema}',
                    '{table}'
                );
                """
                total_records = self.duck_conn.execute(count_query).fetchone()[0]

                # Ottieni lo schema della tabella
                schema_query = f"""
                SELECT column_name, data_type, is_nullable 
                FROM postgres_scan(
                    '{self.pg_conn_string}',
                    'SELECT column_name, data_type, is_nullable 
                    FROM information_schema.columns 
                    WHERE table_schema = ''{self.schema}'' AND table_name = ''{table}''
                    ORDER BY ordinal_position'
                );
                """
                schema_info = self.duck_conn.execute(schema_query).fetchall()

                # Salva lo schema come JSON
                schema_file = backup_path / f"{table}_schema.json"
                schema_data = [
                    {"column_name": row[0], "data_type": row[1], "is_nullable": row[2]}
                    for row in schema_info
                ]
                with open(schema_file, "w") as f:
                    json.dump(schema_data, f)

                # Memorizza le statistiche e il percorso del file
                metadata["tables"][table] = {
                    "records": total_records,
                    "file": f"{table}.parquet",
                    "schema_file": f"{table}_schema.json",
                    "status": "success",
                }

                # Esporta i dati direttamente da PostgreSQL a Parquet
                parquet_file = backup_path / f"{table}.parquet"

                export_query = f"""
                COPY (
                    SELECT * FROM postgres_scan(
                        '{self.pg_conn_string}',
                        '{self.schema}',
                        '{table}'
                    )
                ) TO '{parquet_file}' (FORMAT 'PARQUET');
                """

                self.duck_conn.execute(export_query)

                table_logger.info(
                    "table_backup_completed",
                    records=total_records,
                    file=str(parquet_file),
                )

            except Exception as e:
                table_logger.exception("table_backup_failed", error=str(e))
                metadata["tables"][table] = {"status": "failed", "error": str(e)}

        # Salva i metadati
        metadata_file = backup_path / "metadata.json"
        with open(metadata_file, "w") as f:
            json.dump(metadata, f, default=str)

        # Conta i successi/fallimenti
        success_count = sum(
            1 for t in metadata["tables"].values() if t.get("status") == "success"
        )
        failed_count = sum(
            1 for t in metadata["tables"].values() if t.get("status") == "failed"
        )

        logger.info(
            "postgres_backup_completed",
            backup_dir=str(backup_path),
            total_tables=len(self.tables),
            success_count=success_count,
            failed_count=failed_count,
        )

        return metadata

    async def load_parquet_backup_to_duckdb(
        self, backup_dir: str = None, timestamp: str = None, schema: str = "backup"
    ) -> Dict:
        """Carica un backup Parquet in DuckDB."""
        logger = self.logger.bind(action="load_backup")

        # Trova il timestamp più recente se non specificato
        if backup_dir is None:
            backup_dir = os.path.join(self.backup_base_dir, "postgres_backups")

        if timestamp is None:
            backup_paths = sorted(
                [p for p in Path(backup_dir).iterdir() if p.is_dir()],
                key=lambda p: p.name,
                reverse=True,
            )
            if not backup_paths:
                raise ValueError(f"Nessun backup trovato in {backup_dir}")
            backup_path = backup_paths[0]
            timestamp = backup_path.name
        else:
            backup_path = Path(backup_dir) / timestamp

        if not backup_path.exists():
            raise ValueError(f"Backup {timestamp} non trovato")

        logger.info("loading_parquet_backup", timestamp=timestamp)

        # Leggi i metadati del backup
        metadata_file = backup_path / "metadata.json"
        if not metadata_file.exists():
            raise ValueError(f"File di metadati non trovato in {backup_path}")

        with open(metadata_file, "r") as f:
            metadata = json.load(f)

        # Crea lo schema se non esiste
        self.duck_conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")

        stats = {}

        # Determina quali tabelle caricare
        backup_tables = list(metadata["tables"].keys())

        for table in backup_tables:
            table_logger = logger.bind(table=table)

            if table not in metadata["tables"]:
                table_logger.warning("table_not_in_backup")
                stats[table] = {"status": "skipped", "reason": "not_in_backup"}
                continue

            table_metadata = metadata["tables"][table]
            if table_metadata.get("status") != "success":
                table_logger.warning(
                    "table_backup_was_not_successful",
                    status=table_metadata.get("status"),
                )
                stats[table] = {"status": "skipped", "reason": "backup_not_successful"}
                continue

            parquet_file = backup_path / table_metadata["file"]

            if not parquet_file.exists():
                table_logger.warning("parquet_file_not_found", file=str(parquet_file))
                stats[table] = {"status": "failed", "reason": "file_not_found"}
                continue

            try:
                # Crea la tabella in DuckDB direttamente dal file Parquet
                self.duck_conn.execute(f"""
                CREATE OR REPLACE TABLE {schema}.{table} AS 
                SELECT * FROM read_parquet('{parquet_file}')
                """)

                # Verifica quanti record sono stati caricati
                count = self.duck_conn.execute(
                    f"SELECT COUNT(*) FROM {schema}.{table}"
                ).fetchone()[0]

                stats[table] = {
                    "status": "success",
                    "records": count,
                    "expected": table_metadata.get("records", "unknown"),
                }

                table_logger.info(
                    "table_loaded",
                    records=count,
                    expected=table_metadata.get("records", "unknown"),
                )

            except Exception as e:
                table_logger.exception("table_load_failed", error=str(e))
                stats[table] = {"status": "failed", "reason": str(e)}

        logger.info(
            "parquet_backup_loaded",
            timestamp=timestamp,
            success_count=sum(
                1 for t in stats.values() if t.get("status") == "success"
            ),
        )

        return stats

    async def _convert_value_to_pg_type(self, value: Any, pg_type: str) -> Any:
        """
        Converte un valore al tipo appropriato per PostgreSQL.
        """
        if value is None:
            return None

        # Conversione per tipi specifici
        pg_type = pg_type.lower()

        # Gestione stringa -> bool
        if pg_type in ("boolean", "bool"):
            if isinstance(value, str):
                return value.lower() in ("true", "t", "yes", "y", "1")
            return bool(value)

        # Gestione numeri interi
        if pg_type in ("integer", "int", "int4", "bigint", "int8", "smallint", "int2"):
            if value == "" or value is None:
                return None
            try:
                return int(value)
            except (ValueError, TypeError):
                return None

        # Gestione numeri decimali
        if pg_type in (
            "numeric",
            "decimal",
            "real",
            "double precision",
            "float8",
            "float4",
        ):
            if value == "" or value is None:
                return None
            try:
                return float(value)
            except (ValueError, TypeError):
                return None

        # Per la maggior parte dei tipi, la conversione è diretta
        return value

    async def _prepare_entity_for_pg(
        self, entity: BaseModel, table_name: str, column_types: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """
        Prepara un'entità per l'inserimento in PostgreSQL, convertendo i valori ai tipi appropriati.
        """
        # Ottieni i tipi di colonna se non sono stati forniti
        if column_types is None:
            schema_query = f"""
            SELECT column_name, data_type 
            FROM postgres_scan(
                '{self.pg_conn_string}',
                'SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_schema = ''{self.schema}'' AND table_name = ''{table_name}''
                ORDER BY ordinal_position'
            );
            """
            schema_info = self.duck_conn.execute(schema_query).fetchall()
            column_types = {row[0]: row[1] for row in schema_info}

        # Converti i valori dell'entità
        entity_dict = entity.model_dump()
        result_dict = {}

        for col_name, value in entity_dict.items():
            if col_name in column_types:
                result_dict[col_name] = await self._convert_value_to_pg_type(
                    value, column_types[col_name]
                )
            else:
                # Se la colonna non esiste in PostgreSQL, mantieni il valore originale
                result_dict[col_name] = value

        return result_dict

    async def _sync_cuarcuiu_with_mutation(self, entity_type: Type[BaseModel]):
        """
        Versione che combina le correzioni con la logica di aggiornamento
        """
        logger = self.logger.bind(action="sync_with_mutation")
        try:
            # Ottieni i repository
            duck_repo = self._get_duck_repository(entity_type, "cuarcuiu")
            pg_repo = self._get_pg_repository(entity_type, "cuarcuiu")

            # Usa una query diretta invece di find_all
            schema, table = duck_repo.table_name.split(".")
            query = f"SELECT * FROM {duck_repo.table_name}"
            results = duck_repo.connection.execute(query).fetchall()

            # Ottieni i nomi delle colonne
            cols_query = f"SELECT column_name FROM information_schema.columns WHERE table_schema = '{schema}' AND table_name = '{table}'"
            columns = [
                col[0] for col in duck_repo.connection.execute(cols_query).fetchall()
            ]

            # Crea i record manualmente
            duck_records = []
            for row in results:
                record_dict = dict(zip(columns, row))
                duck_records.append(entity_type(**record_dict))

            # Ottieni i tipi di colonna
            column_types_query = f"""
            SELECT column_name, data_type 
            FROM postgres_scan(
                '{self.pg_conn_string}',
                'information_schema',
                'columns'
            )
            WHERE table_schema = '{self.schema}' AND table_name = 'cuarcuiu'
            ORDER BY ordinal_position;
            """
            column_types = {
                row[0]: row[1]
                for row in self.duck_conn.execute(column_types_query).fetchall()
            }

            # Processa ogni record
            for duck_record in duck_records:
                # Prepara i dati per PostgreSQL
                record_dict = await self._prepare_entity_for_pg(
                    duck_record, "cuarcuiu", column_types
                )

                # Crea una nuova istanza dell'entità
                record = entity_type(**record_dict)

                # Crea un dizionario con le chiavi primarie
                pk_dict = {pk: record_dict[pk] for pk in duck_repo.primary_keys}

                # Verifica se il record esiste già in PostgreSQL
                pg_record = await pg_repo.find_by_id(pk_dict)
                if not pg_record:
                    # Approccio semplificato: cerca direttamente il record precedente
                    prev_pk_dict = pk_dict.copy()
                    prev_pk_dict["progressiv"] = pk_dict["progressiv"] - 1

                    # Cerca il record precedente (potrebbe essere None)
                    try:
                        prev_record = await pg_repo.find_by_id(prev_pk_dict)
                    except Exception as e:
                        logger.warning(
                            f"Errore cercando il record precedente: {str(e)}"
                        )
                        prev_record = None

                    # Se trovato e il record corrente ha mutaz_iniz, aggiorna
                    if (
                        prev_record
                        and hasattr(record, "mutaz_iniz")
                        and record.mutaz_iniz is not None
                        and hasattr(prev_record, "mutaz_fine")
                        and prev_record.mutaz_fine is None
                    ):
                        # Converti in dizionario usando il metodo sicuro
                        try:
                            prev_record_dict = prev_record.model_dump()
                            prev_record_dict["con_eff"] = record.gen_eff
                            prev_record_dict["con_regist"] = record.gen_regist
                            prev_record_dict["con_tipo"] = record.gen_tipo
                            prev_record_dict["con_numero"] = record.gen_numero
                            prev_record_dict["con_progre"] = record.gen_progre
                            prev_record_dict["con_anno"] = record.gen_anno
                            prev_record_dict["mutaz_fine"] = record.mutaz_iniz

                            # Crea una nuova istanza dell'entità
                            updated_prev_record = entity_type(**prev_record_dict)

                            # Aggiorna il record
                            await pg_repo.update(updated_prev_record)
                            self.stats["updated"] += 1
                            logger.info(
                                "updated_previous_record",
                                table="cuarcuiu",
                                progressiv=prev_record.progressiv,
                                mutaz_fine=record.mutaz_iniz,
                            )
                        except Exception as e:
                            logger.warning(
                                f"Errore aggiornando il record precedente: {str(e)}"
                            )

                    # Inserisci il nuovo record
                    await pg_repo.insert(record)
                    self.stats["inserted"] += 1
                    logger.info(
                        "inserted_new_record",
                        table="cuarcuiu",
                        progressiv=record.progressiv,
                    )

            return

        except Exception as e:
            # Log dettagliato dell'errore
            logger.error(
                "error_in_sync_cuarcuiu",
                error_type=type(e).__name__,
                error_message=str(e),
            )
            raise e

    async def _sync_ctpartic_with_mutation(self, entity_type: Type[BaseModel]):
        """
        Versione che combina le correzioni con la logica di aggiornamento
        """
        logger = self.logger.bind(action="sync_with_mutation")
        try:
            # Ottieni i repository
            duck_repo = self._get_duck_repository(entity_type, "ctpartic")
            pg_repo = self._get_pg_repository(entity_type, "ctpartic")

            # Usa una query diretta invece di find_all
            schema, table = duck_repo.table_name.split(".")
            query = f"SELECT * FROM {duck_repo.table_name}"
            results = duck_repo.connection.execute(query).fetchall()

            # Ottieni i nomi delle colonne
            cols_query = f"SELECT column_name FROM information_schema.columns WHERE table_schema = '{schema}' AND table_name = '{table}'"
            columns = [
                col[0] for col in duck_repo.connection.execute(cols_query).fetchall()
            ]

            # Crea i record manualmente
            duck_records = []
            for row in results:
                record_dict = dict(zip(columns, row))
                duck_records.append(entity_type(**record_dict))

            # Ottieni i tipi di colonna
            column_types_query = f"""
            SELECT column_name, data_type 
            FROM postgres_scan(
                '{self.pg_conn_string}',
                'information_schema',
                'columns'
            )
            WHERE table_schema = '{self.schema}' AND table_name = 'ctpartic'
            ORDER BY ordinal_position;
            """
            column_types = {
                row[0]: row[1]
                for row in self.duck_conn.execute(column_types_query).fetchall()
            }

            # Processa ogni record
            for duck_record in duck_records:
                # Prepara i dati per PostgreSQL
                record_dict = await self._prepare_entity_for_pg(
                    duck_record, "ctpartic", column_types
                )

                # Crea una nuova istanza dell'entità
                record = entity_type(**record_dict)

                # Crea un dizionario con le chiavi primarie
                pk_dict = {pk: record_dict[pk] for pk in duck_repo.primary_keys}

                # Verifica se il record esiste già in PostgreSQL
                pg_record = await pg_repo.find_by_id(pk_dict)
                if not pg_record:
                    # Approccio semplificato: cerca direttamente il record precedente
                    prev_pk_dict = pk_dict.copy()
                    prev_pk_dict["progressiv"] = pk_dict["progressiv"] - 1

                    # Cerca il record precedente (potrebbe essere None)
                    try:
                        prev_record = await pg_repo.find_by_id(prev_pk_dict)
                    except Exception as e:
                        logger.warning(
                            f"Errore cercando il record precedente: {str(e)}"
                        )
                        prev_record = None

                    # Se trovato e il record corrente ha mutaz_iniz, aggiorna
                    if (
                        prev_record
                        and hasattr(record, "mutaz_iniz")
                        and record.mutaz_iniz is not None
                        and hasattr(prev_record, "mutaz_fine")
                        and prev_record.mutaz_fine is None
                    ):
                        # Converti in dizionario usando il metodo sicuro
                        try:
                            prev_record_dict = prev_record.model_dump()
                            prev_record_dict["con_eff"] = record.gen_eff
                            prev_record_dict["con_regist"] = record.gen_regist
                            prev_record_dict["con_tipo"] = record.gen_tipo
                            prev_record_dict["con_numero"] = record.gen_numero
                            prev_record_dict["con_progre"] = record.gen_progre
                            prev_record_dict["con_anno"] = record.gen_anno
                            prev_record_dict["mutaz_fine"] = record.mutaz_iniz

                            # Crea una nuova istanza dell'entità
                            updated_prev_record = entity_type(**prev_record_dict)

                            # Aggiorna il record
                            await pg_repo.update(updated_prev_record)
                            self.stats["updated"] += 1
                            logger.info(
                                "updated_previous_record",
                                table="ctpartic",
                                progressiv=prev_record.progressiv,
                                mutaz_fine=record.mutaz_iniz,
                            )
                        except Exception as e:
                            logger.warning(
                                f"Errore aggiornando il record precedente: {str(e)}"
                            )

                    # Inserisci il nuovo record
                    await pg_repo.insert(record)
                    self.stats["inserted"] += 1
                    logger.info(
                        "inserted_new_record",
                        table="ctpartic",
                        progressiv=record.progressiv,
                    )

            return

        except Exception as e:
            # Log dettagliato dell'errore
            logger.error(
                "error_in_sync_ctpartic",
                error_type=type(e).__name__,
                error_message=str(e),
            )
            raise e

    async def _sync_ctfisica_with_update(self, entity_type: Type[BaseModel]):
        """
        Versione che combina le correzioni con la logica di aggiornamento
        """
        logger = self.logger.bind(action="sync_with_update")
        try:
            # Ottieni i repository
            duck_repo = self._get_duck_repository(entity_type, "ctfisica")
            pg_repo = self._get_pg_repository(entity_type, "ctfisica")

            # Usa una query diretta invece di find_all
            schema, table = duck_repo.table_name.split(".")
            query = f"SELECT * FROM {duck_repo.table_name}"
            results = duck_repo.connection.execute(query).fetchall()

            # Ottieni i nomi delle colonne
            cols_query = f"SELECT column_name FROM information_schema.columns WHERE table_schema = '{schema}' AND table_name = '{table}'"
            columns = [
                col[0] for col in duck_repo.connection.execute(cols_query).fetchall()
            ]

            # Crea i record manualmente
            duck_records = []
            for row in results:
                record_dict = dict(zip(columns, row))
                duck_records.append(entity_type(**record_dict))

            # Ottieni i tipi di colonna
            column_types_query = f"""
            SELECT column_name, data_type 
            FROM postgres_scan(
                '{self.pg_conn_string}',
                'information_schema',
                'columns'
            )
            WHERE table_schema = '{self.schema}' AND table_name = 'ctfisica'
            ORDER BY ordinal_position;
            """
            column_types = {
                row[0]: row[1]
                for row in self.duck_conn.execute(column_types_query).fetchall()
            }

            # Processa ogni record
            for duck_record in duck_records:
                # Prepara i dati per PostgreSQL
                record_dict = await self._prepare_entity_for_pg(
                    duck_record, "ctfisica", column_types
                )

                # Crea una nuova istanza dell'entità
                record = entity_type(**record_dict)

                # Crea un dizionario con le chiavi primarie
                pk_dict = {pk: record_dict[pk] for pk in duck_repo.primary_keys}

                # Verifica se il record esiste già in PostgreSQL
                pg_record = await pg_repo.find_by_id(pk_dict)
                if pg_record:
                    # Approccio semplificato se lo trova aggiorna altrimenti inserisce
                    try:
                        await pg_repo.update(record)
                        self.stats["updated"] += 1
                        logger.info(
                            "updated_existing_record",
                            table="ctfisica",
                            soggetto=record.soggetto,
                        )
                    except Exception as e:
                        logger.warning(f"Errore aggiornando il record: {str(e)}")

                else:
                    # Inserisci il nuovo record
                    await pg_repo.insert(record)
                    self.stats["inserted"] += 1
                    logger.info(
                        "inserted_new_record",
                        table="ctfisica",
                        soggetto=record.soggetto,
                    )

            return

        except Exception as e:
            # Log dettagliato dell'errore
            logger.error(
                "error_in_sync_ctfisica",
                error_type=type(e).__name__,
                error_message=str(e),
            )
            raise e

    async def _sync_ctnonfis_with_update(self, entity_type: Type[BaseModel]):
        """
        Versione che combina le correzioni con la logica di aggiornamento
        """
        logger = self.logger.bind(action="sync_with_update")
        try:
            # Ottieni i repository
            duck_repo = self._get_duck_repository(entity_type, "ctnonfis")
            pg_repo = self._get_pg_repository(entity_type, "ctnonfis")

            # Usa una query diretta invece di find_all
            schema, table = duck_repo.table_name.split(".")
            query = f"SELECT * FROM {duck_repo.table_name}"
            results = duck_repo.connection.execute(query).fetchall()

            # Ottieni i nomi delle colonne
            cols_query = f"SELECT column_name FROM information_schema.columns WHERE table_schema = '{schema}' AND table_name = '{table}'"
            columns = [
                col[0] for col in duck_repo.connection.execute(cols_query).fetchall()
            ]

            # Crea i record manualmente
            duck_records = []
            for row in results:
                record_dict = dict(zip(columns, row))
                duck_records.append(entity_type(**record_dict))

            # Ottieni i tipi di colonna
            column_types_query = f"""
            SELECT column_name, data_type 
            FROM postgres_scan(
                '{self.pg_conn_string}',
                'information_schema',
                'columns'
            )
            WHERE table_schema = '{self.schema}' AND table_name = 'ctnonfis'
            ORDER BY ordinal_position;
            """
            column_types = {
                row[0]: row[1]
                for row in self.duck_conn.execute(column_types_query).fetchall()
            }

            # Processa ogni record
            for duck_record in duck_records:
                # Prepara i dati per PostgreSQL
                record_dict = await self._prepare_entity_for_pg(
                    duck_record, "ctnonfis", column_types
                )

                # Crea una nuova istanza dell'entità
                record = entity_type(**record_dict)

                # Crea un dizionario con le chiavi primarie
                pk_dict = {pk: record_dict[pk] for pk in duck_repo.primary_keys}

                # Verifica se il record esiste già in PostgreSQL
                pg_record = await pg_repo.find_by_id(pk_dict)
                if pg_record:
                    # Approccio semplificato se lo trova aggiorna altrimenti inserisce
                    try:
                        await pg_repo.update(record)
                        self.stats["updated"] += 1
                        logger.info(
                            "updated_existing_record",
                            table="ctnonfis",
                            soggetto=record.soggetto,
                        )
                    except Exception as e:
                        logger.warning(f"Errore aggiornando il record: {str(e)}")

                else:
                    # Inserisci il nuovo record
                    await pg_repo.insert(record)
                    self.stats["inserted"] += 1
                    logger.info(
                        "inserted_new_record",
                        table="ctnonfis",
                        soggetto=record.soggetto,
                    )

            return

        except Exception as e:
            # Log dettagliato dell'errore
            logger.error(
                "error_in_sync_ctnonfis",
                error_type=type(e).__name__,
                error_message=str(e),
            )
            raise e

    async def _sync_related_table(self, table_name: str, entity_type: Type[BaseModel]):
        """
        Sincronizza una tabella correlata.
        Usa un approccio che evita duplicati verificando l'esistenza prima dell'inserimento.
        """
        logger = self.logger.bind(table=table_name)
        try:
            # Ottieni i repository
            duck_repo = self._get_duck_repository(entity_type, table_name)

            # Usa find_all() per ottenere i record
            duck_records = await duck_repo.find_all()
            total_records = len(duck_records)

            # Ottieni i tipi di colonna per PostgreSQL
            column_types_query = f"""
            SELECT column_name, data_type 
            FROM postgres_scan(
                '{self.pg_conn_string}',
                'information_schema',
                'columns'
            )
            WHERE table_schema = '{self.schema}' AND table_name = '{table_name}'
            ORDER BY ordinal_position;
            """
            column_types = {
                row[0]: row[1]
                for row in self.duck_conn.execute(column_types_query).fetchall()
            }

            # Statistiche di elaborazione
            processed = 0
            inserted = 0
            skipped = 0
            errors = 0

            # Processa ogni record
            for idx, duck_record in enumerate(duck_records):
                try:
                    # Prepara i dati per PostgreSQL
                    prepared_dict = await self._prepare_entity_for_pg(
                        duck_record, table_name, column_types
                    )

                    # Costruisci una query SQL per verificare l'esistenza del record
                    # Utilizziamo SQL diretto per evitare problemi con i parametri
                    where_parts = []
                    where_params = {}

                    for i, (col, val) in enumerate(prepared_dict.items()):
                        param_name = f"w{i}"  # Uso "w" per distinguere dai parametri di inserimento
                        if val is None:
                            where_parts.append(f'"{col}" IS NULL')
                        else:
                            where_parts.append(f'"{col}" = :{param_name}')
                            where_params[param_name] = val

                    where_clause = " AND ".join(where_parts)
                    count_query = f"SELECT COUNT(*) FROM {self.schema}.{table_name} WHERE {where_clause}"

                    # Esegui la query di conteggio
                    result = self.pg_dal.connection.execute(
                        text(count_query), where_params
                    )
                    count = result.fetchone()[0]

                    if count == 0:
                        # Il record non esiste, inseriscilo
                        columns_str = ", ".join(
                            [f'"{col}"' for col in prepared_dict.keys()]
                        )
                        placeholders = []
                        insert_params = {}

                        for i, (col, val) in enumerate(prepared_dict.items()):
                            param_name = f"p{i}"
                            placeholders.append(f":{param_name}")
                            insert_params[param_name] = val

                        values_str = ", ".join(placeholders)
                        insert_query = f"INSERT INTO {self.schema}.{table_name} ({columns_str}) VALUES ({values_str})"
                        self.pg_dal.connection.execute(
                            text(insert_query), insert_params
                        )

                        inserted += 1
                        self.stats["inserted"] += 1
                    else:
                        # Il record esiste già, lo saltiamo
                        skipped += 1

                    processed += 1

                    # Log periodico
                    if processed % 100 == 0:
                        progress_percent = (processed / total_records) * 100
                        logger.info(
                            f"Progresso sincronizzazione {table_name}: "
                            f"{processed}/{total_records} record ({progress_percent:.1f}%) - "
                            f"Inseriti: {inserted}, Saltati: {skipped}, Errori: {errors}"
                        )

                except Exception as e:
                    errors += 1
                    self.stats["errors"] += 1
                    logger.warning(
                        f"Errore processando record in {table_name} (indice {idx}): {str(e)}"
                    )

            # Log finale
            logger.info(
                f"Sincronizzazione {table_name} completata: "
                f"{processed}/{total_records} record processati "
                f"({inserted} inseriti, {skipped} già esistenti, {errors} errori)"
            )

        except Exception as e:
            # Log dettagliato dell'errore
            logger.error(
                "error_in_sync_related_table",
                table=table_name,
                error_type=type(e).__name__,
                error_message=str(e),
            )
            raise e

    async def validate_data_consistency(self) -> TupleType[bool, List[Dict]]:
        """
        Verifica la consistenza dei dati tra DuckDB e PostgreSQL.

        Returns:
            TupleType[bool, List[Dict]]: (è_coerente, lista_problemi)
        """
        issues = []
        logger = self.logger.bind(action="validate_consistency")
        logger.info("starting_consistency_validation")

        try:
            # Verifica il conteggio dei record
            for table in self.tables:
                duck_count = self.duck_conn.execute(
                    f"SELECT COUNT(*) FROM {self.schema}.{table}"
                ).fetchone()[0]

                pg_count_query = f"""
                SELECT COUNT(*) FROM postgres_scan(
                    '{self.pg_conn_string}',
                    '{self.schema}',
                    '{table}'
                );
                """
                pg_count = self.duck_conn.execute(pg_count_query).fetchone()[0]

                if duck_count != pg_count:
                    logger.warning(
                        "record_count_mismatch",
                        table=table,
                        duck_count=duck_count,
                        pg_count=pg_count,
                    )
                    issues.append(
                        {
                            "type": "record_count_mismatch",
                            "table": table,
                            "duck_count": duck_count,
                            "pg_count": pg_count,
                        }
                    )

            # Verifica la catena di mutazioni per cuarcuiu
            mutation_query = f"""
            SELECT 
                prev.codice, prev.sezione, prev.immobile, prev.tipo_imm, 
                prev.progressiv as prev_progressiv, 
                next.progressiv as next_progressiv,
                prev.mutaz_fine, next.mutaz_iniz
            FROM postgres_scan(
                '{self.pg_conn_string}',
                '{self.schema}',
                'cuarcuiu'
            ) prev
            JOIN postgres_scan(
                '{self.pg_conn_string}',
                '{self.schema}',
                'cuarcuiu'
            ) next
            ON prev.codice = next.codice
            AND prev.sezione = next.sezione
            AND prev.immobile = next.immobile
            AND prev.tipo_imm = next.tipo_imm
            AND prev.progressiv + 1 = next.progressiv
            WHERE prev.mutaz_fine IS NOT NULL 
            AND prev.mutaz_fine != next.mutaz_iniz
            """

            inconsistent_mutations = self.duck_conn.execute(mutation_query).fetchall()

            for row in inconsistent_mutations:
                inconsistency = {
                    "type": "inconsistent_mutation",
                    "codice": row[0],
                    "sezione": row[1],
                    "immobile": row[2],
                    "tipo_imm": row[3],
                    "prev_progressiv": row[4],
                    "next_progressiv": row[5],
                    "mutaz_fine": row[6],
                    "mutaz_iniz": row[7],
                    "description": "Catena di mutazioni inconsistente",
                }
                logger.warning("inconsistent_mutation_chain", **inconsistency)
                issues.append(inconsistency)

            # Verifica integrità referenziale tra cuarcuiu e tabelle correlate
            for related_table in [t for t in self.tables if t != "cuarcuiu"]:
                # Verifica che ogni record nelle tabelle correlate abbia un record corrispondente in cuarcuiu
                orphans_query = f"""
                SELECT rt.codice, rt.sezione, rt.immobile, rt.tipo_imm, rt.progressiv
                FROM postgres_scan(
                    '{self.pg_conn_string}',
                    '{self.schema}',
                    '{related_table}'
                ) rt
                LEFT JOIN postgres_scan(
                    '{self.pg_conn_string}',
                    '{self.schema}',
                    'cuarcuiu'
                ) cu
                ON rt.codice = cu.codice
                AND rt.sezione = cu.sezione
                AND rt.immobile = cu.immobile
                AND rt.tipo_imm = cu.tipo_imm
                AND rt.progressiv = cu.progressiv
                WHERE cu.codice IS NULL
                LIMIT 100
                """

                orphans = self.duck_conn.execute(orphans_query).fetchall()

                if orphans:
                    logger.warning(
                        "orphaned_related_records",
                        table=related_table,
                        count=len(orphans),
                    )
                    for orphan in orphans:
                        issues.append(
                            {
                                "type": "orphaned_record",
                                "table": related_table,
                                "codice": orphan[0],
                                "sezione": orphan[1],
                                "immobile": orphan[2],
                                "tipo_imm": orphan[3],
                                "progressiv": orphan[4],
                                "description": f"Record in {related_table} senza corrispondenza in cuarcuiu",
                            }
                        )

            # Considera i dati coerenti se non ci sono problemi
            is_consistent = len(issues) == 0
            if is_consistent:
                logger.info("data_consistency_validated")
            else:
                logger.warning("data_consistency_issues", issue_count=len(issues))

            return is_consistent, issues

        except Exception as e:
            logger.exception("consistency_validation_failed", error=str(e))
            issues.append(
                {
                    "type": "validation_error",
                    "error": str(e),
                    "description": "Errore durante la validazione della coerenza",
                }
            )
            return False, issues

    async def sync_database(self, entity_types: Dict[str, Type[BaseModel]]):
        """
        Sincronizza tutte le tabelle da DuckDB a PostgreSQL.

        Args:
            entity_types: Dizionario che mappa nomi di tabelle a tipi di entità Pydantic

        Returns:
            Dict: Statistiche sulla sincronizzazione
        """
        logger = self.logger.bind(operation="sync_database")
        logger.info("starting_sync", tables=list(entity_types.keys()))

        if "ctpartic" in entity_types:
            from catasto.postgres.land import update_terreni

            result = await update_terreni(syncer=self, entity_types=entity_types)
            logger.info("terreni", success=result["success"], stats=result["stats"])
            return result

        elif "cuarcuiu" in entity_types:
            from catasto.postgres.building import update_fabbricati

            result = await update_fabbricati(syncer=self, entity_types=entity_types)
            logger.info("fabbricati", success=result["success"], stats=result["stats"])
            return result

        elif "ctfisica" in entity_types:
            from catasto.postgres.subject import update_soggetti

            result = await update_soggetti(syncer=self, entity_types=entity_types)
            logger.info("soggetti", success=result["success"], stats=result["stats"])
            return result

    async def sync_database_with_backup(
        self, entity_types: Dict[str, Type[BaseModel]], validate_after_sync=True
    ):
        """
        Sincronizza tutte le tabelle da DuckDB a PostgreSQL con backup automatico
        e validazione opzionale.

        Args:
            entity_types: Dizionario che mappa nomi di tabelle a tipi di entità Pydantic
            validate_after_sync: Se True, esegue verifiche di coerenza dopo la sincronizzazione

        Returns:
            Dict: Statistiche e risultati della sincronizzazione
        """
        logger = self.logger.bind(operation="sync_with_backup")
        logger.info(
            "starting_sync_with_backup",
            tables=list(entity_types.keys()),
            validate=validate_after_sync,
        )

        # Genera un timestamp per questa sincronizzazione
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        # Backup dello stato pre-sincronizzazione
        try:
            backup_metadata = await self.backup_postgres_to_parquet(timestamp=timestamp)
            logger.info(
                "pre_sync_backup_completed",
                timestamp=timestamp,
                backup_stats={
                    t: m.get("records", 0) for t, m in backup_metadata["tables"].items()
                },
            )
        except Exception as e:
            logger.error("pre_sync_backup_failed", error=str(e))
            return {"success": False, "reason": "backup_failed", "error": str(e)}

        # Inizia una transazione nel database PostgreSQL
        transaction = None
        try:
            # Inizia la transazione
            transaction = self.pg_dal.begin_transaction()
            logger.info("transaction_started")

            # Esegui la sincronizzazione
            # Prima sincronizza la tabella cuarcuiu con la logica di mutazione
            if "cuarcuiu" in self.tables and "cuarcuiu" in entity_types:
                await self._sync_cuarcuiu_with_mutation(entity_types["cuarcuiu"])

            # Poi sincronizza le altre tabelle
            for table in [
                t for t in self.tables if t != "cuarcuiu" and t in entity_types
            ]:
                await self._sync_related_table(table, entity_types[table])

            # Verifica la coerenza dei dati se richiesto
            if validate_after_sync:
                logger.info("validating_data_consistency")
                is_consistent, issues = await self.validate_data_consistency()

                if not is_consistent:
                    logger.error("data_inconsistency_detected", issues=issues)
                    # Esegui il rollback se ci sono problemi di coerenza
                    transaction.rollback()
                    logger.info("transaction_rolled_back")

                    return {
                        "success": False,
                        "rolled_back": True,
                        "issues": issues,
                        "stats": self.stats,
                        "backup_timestamp": timestamp,
                    }

                logger.info("data_consistency_validated")

            # Commit della transazione
            transaction.commit()
            logger.info("transaction_committed", stats=self.stats)

            return {"success": True, "stats": self.stats, "backup_timestamp": timestamp}

        except Exception as e:
            # Rollback in caso di errore
            if transaction:
                transaction.rollback()
                logger.error("transaction_rolled_back_due_to_error", error=str(e))

            self.stats["errors"] += 1
            logger.exception("sync_failed", error=str(e))

            return {
                "success": False,
                "reason": "sync_error",
                "error": str(e),
                "backup_timestamp": timestamp,
            }

    async def restore_from_backup(self, timestamp: str = None):
        """
        Ripristina il database PostgreSQL da un backup Parquet.

        Args:
            timestamp: Timestamp specifico del backup da ripristinare (se None, usa il più recente)

        Returns:
            Dict: Risultati del ripristino
        """
        logger = self.logger.bind(operation="restore_from_backup")
        logger.info("starting_restore", timestamp=timestamp or "latest")

        backup_dir = os.path.join(self.backup_base_dir, "postgres_backups")

        # Se timestamp non è specificato, trova il backup più recente
        if timestamp is None:
            backup_paths = sorted(
                [p for p in Path(backup_dir).iterdir() if p.is_dir()],
                key=lambda p: p.name,
                reverse=True,
            )
            if not backup_paths:
                logger.error("no_backups_found", dir=backup_dir)
                return {"success": False, "reason": "no_backups_found"}
            backup_path = backup_paths[0]
            timestamp = backup_path.name
        else:
            backup_path = Path(backup_dir) / timestamp
            if not backup_path.exists():
                logger.error("backup_not_found", timestamp=timestamp, dir=backup_dir)
                return {"success": False, "reason": "backup_not_found"}

        logger.info("found_backup", path=str(backup_path))

        # Leggi i metadati del backup
        metadata_file = backup_path / "metadata.json"
        if not metadata_file.exists():
            logger.error("metadata_not_found", path=str(metadata_file))
            return {"success": False, "reason": "metadata_not_found"}

        with open(metadata_file, "r") as f:
            metadata = json.load(f)

        # Inizia una transazione PostgreSQL
        transaction = None
        try:
            transaction = self.pg_dal.begin_transaction()
            logger.info("restore_transaction_started")

            # Ripristina ogni tabella
            for table in self.tables:
                if table not in metadata["tables"]:
                    logger.warning("table_not_in_backup", table=table)
                    continue

                table_metadata = metadata["tables"][table]
                if table_metadata.get("status") != "success":
                    logger.warning(
                        "table_backup_was_not_successful",
                        table=table,
                        status=table_metadata.get("status"),
                    )
                    continue

                parquet_file = backup_path / table_metadata["file"]
                if not parquet_file.exists():
                    logger.warning(
                        "parquet_file_not_found", table=table, file=str(parquet_file)
                    )
                    continue

                # Ripristina la tabella da Parquet
                logger.info("restoring_table", table=table)

                # Prima elimina i dati esistenti
                self.pg_dal.execute(text(f"DELETE FROM {self.schema}.{table}"))

                # Crea una tabella temporanea in DuckDB per i dati
                temp_table = f"temp_restore_{table}"
                self.duck_conn.execute(f"""
                CREATE OR REPLACE TABLE {temp_table} AS 
                SELECT * FROM read_parquet('{parquet_file}')
                """)

                # Per ogni record, inserisci in PostgreSQL
                column_names = [
                    col[0]
                    for col in self.duck_conn.execute(
                        f"SELECT column_name FROM information_schema.columns WHERE table_name = '{temp_table}'"
                    ).fetchall()
                ]

                # Ottieni i dati
                restore_data = self.duck_conn.execute(
                    f"SELECT * FROM {temp_table}"
                ).fetchall()

                # Prepara l'istruzione INSERT
                placeholders = ", ".join(["%s" for _ in column_names])
                columns_str = ", ".join([f'"{col}"' for col in column_names])

                insert_query = text(
                    f"INSERT INTO {self.schema}.{table} ({columns_str}) VALUES ({placeholders})"
                )

                # Esegui l'inserimento batch
                batch_size = 1000
                for i in range(0, len(restore_data), batch_size):
                    batch = restore_data[i : i + batch_size]
                    self.pg_dal.execute(insert_query, [list(row) for row in batch])
                    logger.debug(
                        "restore_progress",
                        table=table,
                        records=i + len(batch),
                        total=len(restore_data),
                    )

                logger.info("table_restored", table=table, records=len(restore_data))

                # Elimina la tabella temporanea
                self.duck_conn.execute(f"DROP TABLE IF EXISTS {temp_table}")

            # Commit delle modifiche
            transaction.commit()
            logger.info("restore_completed", timestamp=timestamp)

            return {
                "success": True,
                "timestamp": timestamp,
                "tables_restored": len(
                    [
                        t
                        for t in self.tables
                        if t in metadata["tables"]
                        and metadata["tables"][t].get("status") == "success"
                    ]
                ),
            }

        except Exception as e:
            if transaction:
                transaction.rollback()
                logger.error("restore_transaction_rolled_back", error=str(e))

            logger.exception("restore_failed", error=str(e))
            return {"success": False, "reason": "restore_error", "error": str(e)}
