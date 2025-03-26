import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Generic, List, Optional, Protocol, Type, TypeVar

import sqlalchemy as db
from pydantic import BaseModel
from sqlalchemy import MetaData, Table, inspect, text
from sqlalchemy.dialects.postgresql import insert as pg_insert

# Tipo generico per i modelli di entità
T = TypeVar("T", bound=BaseModel)


# Repository come Protocol
class Repository(Protocol[T]):
    async def insert(self, entity: T) -> None: ...

    async def insert_many(self, entities: List[T]) -> int: ...

    async def update(self, entity: T) -> None: ...

    async def find_by_id(self, id_values: Dict[str, Any]) -> Optional[T]: ...

    async def find_all(self) -> List[T]: ...

    async def find_by_criteria(self, criteria: Dict[str, Any]) -> List[T]: ...


# DataAccessLayer per PostgreSQL usando SQLAlchemy
class PostgresDataAccessLayer:
    def __init__(self, conn_string: str):
        self.conn_string = conn_string
        self.engine = None
        self.connection = None
        self.metadata = MetaData()
        self.inspector = None
        self._tables_cache = {}

    def connect(self):
        """Stabilisce la connessione al database."""
        self.engine = db.create_engine(self.conn_string)
        self.connection = self.engine.connect()
        self.metadata = MetaData(bind=self.connection)
        self.inspector = inspect(self.engine)

    def close(self):
        """Chiude la connessione al database."""
        if self.connection:
            self.connection.close()
        if self.engine:
            self.engine.dispose()

    def get_table(self, table_name: str, schema: str) -> Table:
        """Ottiene un oggetto Table di SQLAlchemy."""
        cache_key = f"{schema}.{table_name}"
        if cache_key not in self._tables_cache:
            self._tables_cache[cache_key] = Table(
                table_name,
                self.metadata,
                autoload=True,
                autoload_with=self.engine,
                schema=schema,
            )
        return self._tables_cache[cache_key]

    def get_schema_names(self) -> List[str]:
        """Ottiene i nomi degli schemi disponibili."""
        return self.inspector.get_schema_names()

    def get_table_names(self, schema: str) -> List[str]:
        """Ottiene i nomi delle tabelle in uno schema."""
        return self.inspector.get_table_names(schema)

    def get_primary_keys(self, table_name: str, schema: str) -> List[str]:
        """Ottiene le chiavi primarie di una tabella."""
        pk_constraint = self.inspector.get_pk_constraint(table_name, schema)
        return pk_constraint["constrained_columns"]

    def execute(self, statement):
        """Esegue una query SQL."""
        return self.connection.execute(statement)

    def begin_transaction(self):
        """Inizia una transazione."""
        return self.connection.begin()


# Repository PostgreSQL che usa SQLAlchemy
class PostgresRepository(Generic[T]):
    def __init__(
        self,
        dal: PostgresDataAccessLayer,
        entity_type: Type[T],
        table_name: str,
        schema: str,
        primary_keys: List[str] = None,
    ):
        self.dal = dal
        self.entity_type = entity_type
        self.table_name = table_name
        self.schema = schema
        self._table = None
        self._primary_keys = primary_keys

    @property
    def table(self) -> Table:
        """Ottiene l'oggetto Table di SQLAlchemy, caricandolo se necessario."""
        if self._table is None:
            self._table = self.dal.get_table(self.table_name, self.schema)
        return self._table

    @property
    def primary_keys(self) -> List[str]:
        """Ottiene le chiavi primarie della tabella."""
        if self._primary_keys is None:
            self._primary_keys = self.dal.get_primary_keys(self.table_name, self.schema)
        return self._primary_keys

    async def _execute_in_thread(self, func, *args, **kwargs):
        """Esegue una funzione in un thread separato per non bloccare l'event loop."""
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            return await loop.run_in_executor(executor, lambda: func(*args, **kwargs))

    async def insert(self, entity: T) -> None:
        """Inserisce una singola entità nel database."""
        await self.insert_many([entity])

    async def insert_many(self, entities: List[T]) -> int:
        """
        Inserisce molte entità nel database.

        Returns:
            int: Il numero di record inseriti
        """
        if not entities:
            return 0

        def do_insert():
            records = [entity.model_dump() for entity in entities]
            ins = self.table.insert().values(records)
            result = self.dal.execute(ins)
            return result.rowcount

        return await self._execute_in_thread(do_insert)

    async def update(self, entity: T) -> None:
        """Aggiorna un'entità esistente nel database."""
        if not self.primary_keys:
            raise ValueError("Impossibile aggiornare senza chiavi primarie")

        def do_update():
            record = entity.model_dump()

            # Costruisci la condizione WHERE basata sulle chiavi primarie
            conditions = []
            for pk in self.primary_keys:
                conditions.append(getattr(self.table.c, pk) == record[pk])

            # Prepara l'update con i valori da aggiornare
            update_values = {
                k: v for k, v in record.items() if k not in self.primary_keys
            }

            # Esegui l'update
            upd = self.table.update().where(db.and_(*conditions)).values(update_values)
            result = self.dal.execute(upd)
            return result.rowcount

        return await self._execute_in_thread(do_update)

    async def find_by_id(self, id_values: Dict[str, Any]) -> Optional[T]:
        """
        Trova un'entità tramite la sua chiave primaria.

        Args:
            id_values: Dizionario che mappa i nomi delle chiavi primarie ai loro valori

        Returns:
            L'entità trovata o None se non esiste
        """
        if not self.primary_keys:
            raise ValueError("Impossibile cercare per ID senza chiavi primarie")

        def do_find():
            try:
                # Costruisci le condizioni per la query
                conditions = []
                for pk in self.primary_keys:
                    if pk not in id_values:
                        raise ValueError(
                            f"Manca il valore per la chiave primaria: {pk}"
                        )
                    conditions.append(getattr(self.table.c, pk) == id_values[pk])

                # Esegui la query
                query = db.select(self.table).where(db.and_(*conditions))
                result = self.dal.execute(query).fetchone()

                if result:
                    # Ottieni i nomi delle colonne dalla tabella
                    column_names = [col.name for col in self.table.columns]

                    # Crea un dizionario abbinando nomi di colonna ai valori
                    record = dict(zip(column_names, result))

                    # Crea l'entità
                    return self.entity_type(**record)
                return None
            except Exception as e:
                print(f"Errore in find_by_id: {type(e).__name__}: {str(e)}")
                return None

        return await self._execute_in_thread(do_find)

    async def find_all(self) -> List[T]:
        """
        Trova tutte le entità nella tabella.

        Returns:
            Lista di tutte le entità
        """

        def do_find_all():
            query = db.select(self.table)
            result = self.dal.execute(query).fetchall()

            entities = []
            for row in result:
                record = dict(row)
                entities.append(self.entity_type(**record))

            return entities

        return await self._execute_in_thread(do_find_all)

    async def find_by_criteria(self, criteria: Dict[str, Any]) -> List[T]:
        """
        Trova entità che soddisfano determinati criteri.

        Args:
            criteria: Dizionario con coppie chiave-valore per filtrare i risultati

        Returns:
            Lista di entità che soddisfano i criteri
        """

        def do_find_by_criteria():
            conditions = []
            for key, value in criteria.items():
                if hasattr(self.table.c, key):
                    conditions.append(getattr(self.table.c, key) == value)

            query = db.select(self.table)
            if conditions:
                query = query.where(db.and_(*conditions))

            result = self.dal.execute(query).fetchall()

            entities = []
            for row in result:
                record = dict(row)
                entities.append(self.entity_type(**record))

            return entities

        return await self._execute_in_thread(do_find_by_criteria)

    async def find_by_custom_where(
        self, condition_str: str, params: Dict[str, Any] = None
    ) -> List[T]:
        """
        Trova entità usando una condizione WHERE personalizzata.

        Args:
            condition_str: Stringa di condizione WHERE (es. "column1 < :val1 AND column2 = :val2")
            params: Parametri per la condizione

        Returns:
            Lista di entità che soddisfano la condizione
        """

        def do_find_custom():
            query = text(
                f"SELECT * FROM {self.schema}.{self.table_name} WHERE {condition_str}"
            )
            # Cambia il modo in cui i parametri vengono passati
            if params:
                result = self.dal.execute(query, **params).fetchall()
            else:
                result = self.dal.execute(query).fetchall()

            entities = []
            for row in result:
                # Converti i valori di riga in un dizionario
                if hasattr(row, "_asdict"):  # RowProxy
                    record = row._asdict()
                else:  # Per risultati di text()
                    record = dict(zip(row.keys(), row))

                entities.append(self.entity_type(**record))

            return entities

        return await self._execute_in_thread(do_find_custom)

    async def upsert(self, entity: T, update_fields: List[str] = None) -> None:
        """
        Inserisce o aggiorna un'entità (upsert) usando la sintassi di PostgreSQL.

        Args:
            entity: Entità da inserire o aggiornare
            update_fields: Campi da aggiornare (se None, aggiorna tutti i campi tranne le chiavi primarie)
        """

        def do_upsert():
            record = entity.model_dump()

            # Crea la query di insert
            insert_stmt = pg_insert(self.table).values(record)

            # Determina i campi da aggiornare
            if update_fields is None:
                update_fields = [
                    col for col in record.keys() if col not in self.primary_keys
                ]

            # Crea il dizionario di aggiornamento
            update_dict = {col: insert_stmt.excluded[col] for col in update_fields}

            # Crea la query di upsert
            upsert_stmt = insert_stmt.on_conflict_do_update(
                index_elements=self.primary_keys, set_=update_dict
            )

            # Esegui la query
            result = self.dal.execute(upsert_stmt)
            return result.rowcount

        return await self._execute_in_thread(do_upsert)
