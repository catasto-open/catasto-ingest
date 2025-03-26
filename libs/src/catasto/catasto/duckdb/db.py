import asyncio
from typing import Any, Dict, Type, Union

import duckdb
from pydantic import BaseModel

from catasto.duckdb.repository import DuckDBRepository, Repository, T
from catasto.schemas.carto import LandSheet
from catasto.schemas.census import Census

from ..writer import LocalWriterService


class DuckDBManager:
    def __init__(self, duckdb_path: str, dal: Any):
        self.duckdb_path = duckdb_path
        self.dal = dal
        self.conn = None
        self.repositories = {}

    def connect(self) -> duckdb.DuckDBPyConnection:
        """Stabilisce una connessione al database DuckDB."""
        if self.conn is None:
            self.conn = duckdb.connect(self.duckdb_path)
        return self.conn

    def close(self) -> None:
        """Chiude la connessione al database DuckDB."""
        if self.conn is not None:
            self.conn.close()
            self.conn = None

    def create_table_from_sqlalchemy(self, sa_table, schema: str) -> str:
        """Crea una tabella DuckDB basata su una tabella SQLAlchemy."""
        # Implementazione come nella versione precedente
        # ...
        duck_table_name = f"{schema}_{sa_table.name}"
        return duck_table_name

    def get_repository(
        self, entity_type: Type[T], schema: str, table_name: str
    ) -> Repository[T]:
        """
        Ottiene un repository per un tipo di entità e una tabella specifica.
        Se il repository non esiste, lo crea.
        """
        key = f"{schema}.{table_name}"

        if key not in self.repositories:
            # Assicurati che la connessione sia stabilita
            self.connect()

            # Ottieni la tabella da SQLAlchemy
            sa_table = self.dal.get_table(table_name, schema)

            # Crea la tabella in DuckDB se non esiste già
            # Usa il formato schema.tabella invece di schema_tabella
            duck_table_name = f"{schema}.{table_name}"

            # Estrai le chiavi primarie
            primary_keys = [col.name for col in sa_table.primary_key.columns]

            # Crea e memorizza il repository
            self.repositories[key] = DuckDBRepository(
                connection=self.conn,
                entity_type=entity_type,
                table_name=duck_table_name,
                primary_keys=primary_keys,
            )

        return self.repositories[key]


class DuckDBWriter(LocalWriterService):
    def __init__(
        self,
        store: Union[LandSheet, Census],
        duck_manager: DuckDBManager,
        entity_type_mapping: Dict[str, Type[BaseModel]] = None,
    ):
        super().__init__(store)
        self.duck_manager = duck_manager
        # Mappatura da nomi di attributi Census a tipi di entità
        self.entity_type_mapping = entity_type_mapping or {}

    async def write(self) -> duckdb.DuckDBPyConnection:
        """
        Scrive i dati del Census su DuckDB utilizzando repository.

        Returns:
            duckdb.DuckDBPyConnection: La connessione DuckDB su cui sono stati scritti i dati
        """
        try:
            # Sincronizza ogni tabella utilizzando i repository
            tasks = []

            for model_key in dir(self._store):
                # Salta attributi privati e metodi
                if model_key.startswith("_") or callable(
                    getattr(self._store, model_key)
                ):
                    continue

                # Ottieni i dati della tabella
                table_data = getattr(self._store, model_key)

                # Salta se non è una lista o è vuota
                if not isinstance(table_data, list) or not table_data:
                    continue

                # Determina schema e nome tabella
                if "_" in model_key:
                    schema, table_name = model_key.split("_", 1)
                else:
                    schema = "public"
                    table_name = model_key

                # Determina il tipo di entità
                entity_type = self.entity_type_mapping.get(model_key)
                if entity_type is None and table_data:
                    # Se non specificato, usa il tipo del primo elemento
                    entity_type = type(table_data[0])

                if entity_type:
                    # Ottieni il repository per questa entità
                    repo = self.duck_manager.get_repository(
                        entity_type, schema, table_name
                    )

                    # Avvia il task di sincronizzazione usando upsert_many
                    task = repo.upsert_many(table_data)
                    tasks.append(task)

            # Attendi il completamento di tutti i task
            await asyncio.gather(*tasks)

            # Restituisci la connessione
            return self.duck_manager.conn

        except Exception as e:
            # In caso di errore, rilancia l'eccezione
            raise e
