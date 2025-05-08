import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Generic, List, Optional, Protocol, Type, TypeVar

import duckdb
from pydantic import BaseModel

# Tipo generico per i modelli di entità
T = TypeVar("T", bound=BaseModel)


# Repository come Protocol
class Repository(Protocol[T]):
    async def insert(self, entity: T) -> None: ...

    async def insert_many(self, entities: List[T]) -> int: ...

    async def update(self, entity: T) -> None: ...

    async def upsert(self, entity: T) -> None: ...

    async def upsert_many(self, entities: List[T]) -> int: ...

    async def delete(self, entity: T) -> None: ...

    async def find_by_id(self, id_values: Dict[str, Any]) -> Optional[T]: ...

    async def find_all(self) -> List[T]: ...


# Implementazione di repository per DuckDB
class DuckDBRepository(Generic[T]):
    def __init__(
        self,
        connection: duckdb.DuckDBPyConnection,
        entity_type: Type[T],
        table_name: str,
        primary_keys: List[str],
    ):
        self.connection = connection
        self.entity_type = entity_type
        self.table_name = table_name
        self.primary_keys = primary_keys

    async def _execute_in_thread(self, func, *args, **kwargs):
        """Esegue una funzione in un thread separato per non bloccare l'event loop."""
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            return await loop.run_in_executor(executor, lambda: func(*args, **kwargs))

    async def insert(self, entity: T) -> None:
        """Inserisce una singola entità nel database."""
        count = await self.insert_many([entity])
        return count

    async def insert_many(self, entities: List[T]) -> int:
        """
        Inserisce molte entità nel database.

        Returns:
            int: Il numero di record inseriti
        """
        if not entities:
            return 0

        # Converti i modelli Pydantic in dizionari
        records = [entity.model_dump() for entity in entities]

        # Definisci la funzione di inserimento che verrà eseguita nel thread
        # Nella classe DuckDBRepository, metodo insert_many
        def do_insert():
            count = 0
            for record in records:
                columns = ", ".join([f'"{col}"' for col in record.keys()])

                # Costruisci i placeholder con trattamento speciale per le colonne geometry
                placeholders = []
                values = []

                for col, val in record.items():
                    if col.lower() == "geom" and val is not None:
                        # Se è una colonna di tipo geometry, usa ST_GeomFromText
                        placeholders.append("ST_GeomFromText(?)")
                    elif col.lower() in ["t_pt_ins", "t_ln_anc"] and val is not None:
                        # Anche per altre colonne geometry
                        placeholders.append("ST_GeomFromText(?)")
                    else:
                        placeholders.append("?")

                    values.append(val)

                placeholders_str = ", ".join(placeholders)

                query = f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders_str})"

                # Debug: stampa la query e i primi 100 caratteri di ogni valore
                # print(f"Query: {query}")
                # print(
                #     f"Values: {[str(v)[:100] + '...' if isinstance(v, str) and len(str(v)) > 100 else v for v in values]}"
                # )

                try:
                    self.connection.execute(query, values)
                    count += 1
                except Exception as e:
                    print(f"Errore nell'inserimento del record: {e}")
                    # Stampa dettagli aggiuntivi per facilitare il debug
                    for col, val in record.items():
                        if (
                            col.lower() in ["geom", "t_pt_ins", "t_ln_anc"]
                            and val is not None
                        ):
                            print(
                                f"Colonna: {col}, Valore WKT (primi 100 caratteri): {str(val)[:100]}"
                            )
                    continue

            return count

        # Esegui la funzione nel thread e attendi il risultato
        return await self._execute_in_thread(do_insert)

    async def update(self, entity: T) -> None:
        """Aggiorna un'entità esistente nel database."""
        if not self.primary_keys:
            raise ValueError("Impossibile aggiornare senza chiavi primarie")

        record = entity.model_dump()

        def do_update():
            # Costruisci la condizione WHERE basata sulle chiavi primarie
            where_conditions = " AND ".join([f'"{pk}" = ?' for pk in self.primary_keys])
            where_values = [record[pk] for pk in self.primary_keys]

            # Costruisci la clausola SET per i campi non-PK
            set_items = []
            set_values = []
            for col, val in record.items():
                if col not in self.primary_keys:
                    set_items.append(f'"{col}" = ?')
                    set_values.append(val)

            if not set_items:
                return 0  # Niente da aggiornare

            # Crea ed esegui la query
            query = f"UPDATE {self.table_name} SET {', '.join(set_items)} WHERE {where_conditions}"
            self.connection.execute(query, set_values + where_values)
            return 1

        return await self._execute_in_thread(do_update)

    async def upsert(self, entity: T) -> None:
        """Inserisce o aggiorna un'entità nel database."""
        count = await self.upsert_many([entity])
        return count

    async def upsert_many(self, entities: List[T]) -> int:
        """
        Inserisce o aggiorna molte entità nel database.

        Returns:
            int: Il numero di record inseriti o aggiornati
        """
        if not entities:
            return 0

        if not self.primary_keys:
            # Se non ci sono chiavi primarie, esegui solo INSERT
            return await self.insert_many(entities)

        # Converti i modelli Pydantic in dizionari
        records = [entity.model_dump() for entity in entities]

        # Definisci la funzione che verrà eseguita nel thread
        def do_upsert():
            # Crea una tabella temporanea con un nome univoco per evitare conflitti
            task_id = (
                id(asyncio.current_task()) if asyncio.current_task() else id(records)
            )
            temp_table = f"temp_{self.table_name}_{task_id}"

            try:
                # Crea tabella temporanea con la stessa struttura
                self.connection.execute(
                    f"CREATE TEMP TABLE {temp_table} AS SELECT * FROM {self.table_name} WHERE 1=0"
                )

                # Inserisci i record nella tabella temporanea
                for record in records:
                    columns = ", ".join([f'"{col}"' for col in record.keys()])
                    placeholders = ", ".join(["?" for _ in record])
                    self.connection.execute(
                        f"INSERT INTO {temp_table} ({columns}) VALUES ({placeholders})",
                        list(record.values()),
                    )

                # Conta i record prima dell'operazione
                count_before = self.connection.execute(
                    f"SELECT COUNT(*) FROM {self.table_name}"
                ).fetchone()[0]

                # Esegui l'UPDATE per i record esistenti
                pk_conditions = " AND ".join(
                    [f't."{pk}" = s."{pk}"' for pk in self.primary_keys]
                )
                non_pk_columns = [
                    col for col in records[0].keys() if col not in self.primary_keys
                ]

                if non_pk_columns:
                    set_clause = ", ".join(
                        [f't."{col}" = s."{col}"' for col in non_pk_columns]
                    )
                    update_query = f"""
                    UPDATE {self.table_name} t
                    SET {set_clause}
                    FROM {temp_table} s
                    WHERE {pk_conditions}
                    """
                    self.connection.execute(update_query)

                # Esegui l'INSERT per i record nuovi
                insert_conditions = []
                for pk in self.primary_keys:
                    insert_conditions.append(f"""
                    NOT EXISTS (
                        SELECT 1 FROM {self.table_name} t
                        WHERE t."{pk}" = s."{pk}"
                    )
                    """)

                # Combina le condizioni per l'INSERT
                if len(insert_conditions) > 1:
                    final_condition = f"({' OR '.join(insert_conditions)})"
                else:
                    final_condition = insert_conditions[0]

                insert_query = f"""
                INSERT INTO {self.table_name}
                SELECT * FROM {temp_table} s
                WHERE {final_condition}
                """
                self.connection.execute(insert_query)

                # Conta i record dopo l'operazione
                count_after = self.connection.execute(
                    f"SELECT COUNT(*) FROM {self.table_name}"
                ).fetchone()[0]

                # Restituisci il numero di record inseriti
                return (
                    count_after - count_before + len(records)
                )  # Approssimazione degli aggiornamenti

            finally:
                # Elimina la tabella temporanea
                self.connection.execute(f"DROP TABLE IF EXISTS {temp_table}")

        return await self._execute_in_thread(do_upsert)

    async def delete(self, entity: T) -> None:
        """Elimina un'entità dal database."""
        if not self.primary_keys:
            raise ValueError("Impossibile eliminare senza chiavi primarie")

        record = entity.model_dump()

        def do_delete():
            # Costruisci la condizione WHERE basata sulle chiavi primarie
            where_conditions = " AND ".join([f'"{pk}" = ?' for pk in self.primary_keys])
            where_values = [record[pk] for pk in self.primary_keys]

            # Crea ed esegui la query
            query = f"DELETE FROM {self.table_name} WHERE {where_conditions}"
            self.connection.execute(query, where_values)
            return 1

        return await self._execute_in_thread(do_delete)

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

        # Verifica che tutte le chiavi primarie siano fornite
        for pk in self.primary_keys:
            if pk not in id_values:
                raise ValueError(f"Manca il valore per la chiave primaria: {pk}")

        def do_find():
            try:
                # Costruisci la condizione WHERE basata sulle chiavi primarie
                where_conditions = " AND ".join(
                    [f'"{pk}" = ?' for pk in self.primary_keys]
                )
                where_values = [id_values[pk] for pk in self.primary_keys]

                # Crea ed esegui la query
                query = f"SELECT * FROM {self.table_name} WHERE {where_conditions}"
                result = self.connection.execute(query, where_values).fetchone()

                if result:
                    # Ottieni i nomi delle colonne in modo più sicuro
                    if "." in self.table_name:
                        schema, table = self.table_name.split(".")
                        cols_query = f"SELECT column_name FROM information_schema.columns WHERE table_schema = '{schema}' AND table_name = '{table}'"
                        columns = [
                            col[0]
                            for col in self.connection.execute(cols_query).fetchall()
                        ]
                    else:
                        columns = [
                            col[0]
                            for col in self.connection.execute(
                                f"PRAGMA table_info({self.table_name})"
                            ).fetchall()
                        ]

                    # Crea il dizionario e il modello
                    record = dict(zip(columns, result))
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
            try:
                # Ottieni i nomi delle colonne in modo più sicuro
                if "." in self.table_name:
                    schema, table = self.table_name.split(".")
                    cols_query = f"SELECT column_name FROM information_schema.columns WHERE table_schema = '{schema}' AND table_name = '{table}'"
                    columns = [
                        col[0] for col in self.connection.execute(cols_query).fetchall()
                    ]
                else:
                    columns = [
                        col[0]
                        for col in self.connection.execute(
                            f"PRAGMA table_info({self.table_name})"
                        ).fetchall()
                    ]

                # Esegui la query
                query = f"SELECT * FROM {self.table_name}"
                results = self.connection.execute(query).fetchall()

                # Converti i risultati in modelli Pydantic
                entities = []
                for row in results:
                    record = dict(zip(columns, row))
                    entities.append(self.entity_type(**record))

                return entities
            except Exception as e:
                print(f"Errore in find_all: {type(e).__name__}: {str(e)}")
                return []

        return await self._execute_in_thread(do_find_all)
