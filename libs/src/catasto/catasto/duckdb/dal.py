import re

import duckdb
import sqlalchemy as db
from sqlalchemy import (
    BigInteger,
    Column,
    Integer,
    MetaData,
    PrimaryKeyConstraint,
    String,
    Table,
    inspect,
)


class DataAccessLayer:
    connection = None
    engine = None
    conn_string = None
    metadata = db.MetaData()
    inspector = None

    def db_init(self, conn_string):
        self.engine = db.create_engine(conn_string or self.conn_string)
        self.connection = self.engine.connect()
        self.metadata = db.MetaData(bind=self.connection)
        self.inspector = inspect(self.engine)

    def get_table(self, table_name, schema):
        return db.Table(
            table_name,
            self.metadata,
            autoload=True,
            autoload_with=self.engine,
            schema=schema,
        )

    def get_schema_names(self):
        return self.inspector.get_schema_names()

    def get_table_names(self, schema):
        return self.inspector.get_table_names(schema)


class DuckDBDirectDataAccessLayer(DataAccessLayer):
    """
    DataAccessLayer che usa DuckDB direttamente per creare tabelle dalla DDL
    e ne espone la struttura tramite SQLAlchemy.
    """

    def __init__(self, ddl_content=None, duckdb_path=":memory:"):
        """
        Inizializza il DAL con contenuto DDL SQL.

        Args:
            ddl_content: Stringa contenente DDL SQL
            duckdb_path: Percorso del file DuckDB (default: database in memoria)
        """
        self.ddl_content = ddl_content
        self.duckdb_path = duckdb_path
        self.duck_conn = None
        self.metadata = MetaData()
        self.tables = {}

        # Per compatibilità con l'interfaccia DAL
        self.conn_string = None
        self.connection = None
        self.engine = None

    def load_ddl_content(self):
        """Carica ed esegue il contenuto DDL direttamente in DuckDB."""
        if not self.ddl_content:
            return

        # Inizializza connessione DuckDB
        self.duck_conn = duckdb.connect(self.duckdb_path)

        try:
            # Estrai informazioni dalla DDL
            schema_name, table_name, columns, primary_keys = self._parse_ddl(
                self.ddl_content
            )

            # Crea lo schema se non esiste
            self.duck_conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")

            # Esegui il DDL modificato per DuckDB
            modified_ddl = self._adapt_ddl_for_duckdb(self.ddl_content)
            self.duck_conn.execute(modified_ddl)

            # Crea il modello SQLAlchemy della tabella
            self._create_sqlalchemy_model(
                schema_name, table_name, columns, primary_keys
            )

        except Exception as e:
            print(f"Errore nel caricamento DDL: {str(e)}")
            raise

    def _parse_ddl(self, ddl):
        """Estrae informazioni dal DDL."""
        # Estrai schema e nome tabella, supportando anche IF NOT EXISTS
        match = re.search(r"CREATE TABLE\s+(?:IF NOT EXISTS\s+)?(\w+)\.(\w+)", ddl)
        if not match:
            raise ValueError("Impossibile estrarre schema e nome tabella dalla DDL")

        schema_name = match.group(1)
        table_name = match.group(2)

        # Estrai definizioni delle colonne
        columns_section = re.search(r"\((.*?)\);", ddl, re.DOTALL)
        if not columns_section:
            raise ValueError(
                "Impossibile estrarre le definizioni delle colonne dalla DDL"
            )

        columns_text = columns_section.group(1)

        # Estrai chiavi primarie
        pk_match = re.search(
            r"CONSTRAINT \w+ PRIMARY KEY \(\s*(.*?)\s*\)", columns_text
        )
        primary_keys = []
        if pk_match:
            # Rimuovi virgole e pulisci i nomi delle colonne
            primary_keys = [
                pk.strip().replace(",", "").strip()
                for pk in pk_match.group(1).split(",")
            ]

        # Estrai dettagli delle colonne
        columns = {}
        # Rimuovi la definizione di vincolo PK per evitare confusione nell'analisi
        if pk_match:
            columns_text = columns_text.replace(pk_match.group(0), "")

        # Dividi le definizioni delle colonne
        column_defs = re.findall(r"(\w+)\s+([^,]+?)(?:,|$)", columns_text)
        for col_name, col_type in column_defs:
            columns[col_name.strip()] = col_type.strip()

        return schema_name, table_name, columns, primary_keys

    def _adapt_ddl_for_duckdb(self, ddl):
        """Adatta il DDL PostgreSQL per funzionare con DuckDB."""
        # Sostituisci tipi di dati PostgreSQL con equivalenti DuckDB
        ddl = re.sub(r"int8\b", "BIGINT", ddl, flags=re.IGNORECASE)
        ddl = re.sub(r"int4\b", "INTEGER", ddl, flags=re.IGNORECASE)

        # Converti bigserial in BIGINT
        ddl = re.sub(r"\bbigserial\b", "BIGINT", ddl, flags=re.IGNORECASE)

        # Converti anche serial in INTEGER
        ddl = re.sub(r"\bserial\b", "INTEGER", ddl, flags=re.IGNORECASE)

        # Aggiungi IF NOT EXISTS se non è già presente
        if "IF NOT EXISTS" not in ddl:
            ddl = re.sub(r"CREATE TABLE", "CREATE TABLE IF NOT EXISTS", ddl)

        # Rimuovi commenti che potrebbero non essere supportati
        ddl = re.sub(r"COMMENT ON TABLE.*?;", "", ddl, flags=re.DOTALL)

        return ddl

    def _create_sqlalchemy_model(self, schema_name, table_name, columns, primary_keys):
        """Crea un modello SQLAlchemy per la tabella."""
        table_columns = []

        # Mappa i tipi SQL ai tipi SQLAlchemy
        type_map = {
            "varchar": String,
            "INTEGER": Integer,
            "BIGINT": BigInteger,
            "bigserial": BigInteger,
            "serial": Integer,
            "int8": BigInteger,
            "int4": Integer,
        }

        # Crea le colonne SQLAlchemy
        for col_name, col_def in columns.items():
            # Analizza il tipo e gli attributi
            type_match = re.search(r"(\w+)(?:\((\d+)\))?", col_def)
            if not type_match:
                continue

            col_type = type_match.group(1).lower()
            col_length = type_match.group(2)

            # Determina il tipo SQLAlchemy
            if col_type in type_map:
                if col_length and col_type == "varchar":
                    sa_type = type_map[col_type](int(col_length))
                else:
                    sa_type = type_map[col_type]
            else:
                sa_type = String  # Tipo predefinito

            # Controlla se è nullable
            nullable = "NOT NULL" not in col_def

            # Crea la colonna
            column = Column(col_name, sa_type, nullable=nullable)
            table_columns.append(column)

        # Crea la tabella SQLAlchemy
        table = Table(
            table_name,
            self.metadata,
            *table_columns,
            PrimaryKeyConstraint(*primary_keys),
            schema=schema_name,
        )

        self.tables[(schema_name, table_name)] = table

    def initialize(self):
        """Inizializza il DAL caricando il DDL."""
        self.load_ddl_content()

    def get_table(self, table_name, schema):
        """Restituisce l'oggetto Table di SQLAlchemy."""
        return self.tables.get((schema, table_name))

    def get_schema_names(self):
        """Restituisce gli schemi disponibili."""
        schemas = set()
        for schema, _ in self.tables.keys():
            schemas.add(schema)
        return list(schemas)

    def get_table_names(self, schema):
        """Restituisce i nomi delle tabelle in uno schema."""
        tables = []
        for s, t in self.tables.keys():
            if s == schema:
                tables.append(t)
        return tables

    def cleanup(self):
        """Pulisce le risorse."""
        if self.duck_conn:
            self.duck_conn.close()
            self.duck_conn = None
