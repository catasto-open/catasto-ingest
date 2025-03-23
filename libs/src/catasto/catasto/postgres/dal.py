from typing import List

import sqlalchemy as db
import structlog
from sqlalchemy import MetaData, Table, inspect


# DataAccessLayer per PostgreSQL usando SQLAlchemy
class PostgresDataAccessLayer:
    def __init__(self, conn_string: str):
        self.conn_string = conn_string
        self.engine = None
        self.connection = None
        self.metadata = MetaData()
        self.inspector = None
        self._tables_cache = {}
        self.logger = structlog.get_logger().bind(component="PostgresDAL")

    def connect(self):
        """Stabilisce la connessione al database."""
        self.logger.info("connecting_to_database")
        self.engine = db.create_engine(self.conn_string)
        self.connection = self.engine.connect()
        self.metadata = MetaData()
        self.inspector = inspect(self.engine)
        self.logger.info("connection_established")

    def close(self):
        """Chiude la connessione al database."""
        if self.connection:
            self.connection.close()
        if self.engine:
            self.engine.dispose()
        self.logger.info("connection_closed")

    def get_table(self, table_name: str, schema: str) -> Table:
        """Ottiene un oggetto Table di SQLAlchemy."""
        cache_key = f"{schema}.{table_name}"
        if cache_key not in self._tables_cache:
            self.logger.debug("loading_table_metadata", table=cache_key)
            # Usa reflection con l'engine in modo esplicito
            self._tables_cache[cache_key] = Table(
                table_name,
                self.metadata,
                autoload_with=self.engine,  # Usa l'engine invece di dipendere da bind
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

    def execute(self, statement, parameters=None):
        """
        Esegue una query SQL con parametri opzionali.

        Args:
            statement: Query SQL (testo o oggetto SQLAlchemy)
            parameters: Parametri per la query (dict, list, tuple o None)

        Returns:
            Risultato dell'esecuzione
        """
        try:
            if parameters is None:
                return self.connection.execute(statement)
            else:
                # Gestione dei diversi tipi di parametri
                if isinstance(parameters, dict):
                    # Parametri come dizionario (per query con named parameters)
                    return self.connection.execute(statement, parameters)
                elif isinstance(parameters, (list, tuple)):
                    if len(parameters) > 0 and isinstance(parameters[0], dict):
                        # Lista di dizionari (per executemany)
                        return self.connection.execute(statement, *parameters)
                    else:
                        # Lista o tupla di valori (per query con ? o %s)
                        return self.connection.execute(statement, parameters)
                else:
                    # Singolo valore
                    return self.connection.execute(statement, (parameters,))
        except Exception as e:
            self.logger.error(
                "query_execution_error",
                error=str(e),
                query=str(statement),
                parameters=str(parameters),
            )
            raise

    def execute_scalar(self, statement, parameters=None):
        """
        Esegue una query SQL e restituisce un singolo valore scalare.

        Args:
            statement: Query SQL
            parameters: Parametri per la query

        Returns:
            Valore scalare o None
        """
        result = self.execute(statement, parameters)
        row = result.fetchone()
        return row[0] if row else None

    def execute_many(self, statement, parameters_list):
        """
        Esegue una query SQL più volte con diversi parametri.

        Args:
            statement: Query SQL
            parameters_list: Lista di parametri

        Returns:
            Risultato dell'esecuzione
        """
        return self.connection.execute(statement, parameters_list)

    def begin_transaction(self):
        """Inizia una transazione."""
        return self.connection.begin()
