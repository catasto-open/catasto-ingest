import asyncio

from catasto.postgres.db import DatabaseSynchronizer
from catasto.schemas.catastodb.models import (
    Cuarcuiu,
    Cuidenti,
    Cuindiri,
    Curiserv,
    Cuutilit,
)


# Esempio di utilizzo
async def sync_duckdb_to_postgres():
    """Funzione principale per la sincronizzazione da DuckDB a PostgreSQL."""

    # Configura i parametri di connessione
    duckdb_path = "/tmp/catasto.duckdb"
    pg_conn_string = "postgresql://siscatsrv:siscatsrv@localhost:5433/siscat"

    # Mappa le tabelle ai tipi di entità
    entity_types = {
        "cuarcuiu": Cuarcuiu,
        "cuidenti": Cuidenti,
        "cuindiri": Cuindiri,
        "curiserv": Curiserv,
        "cuutilit": Cuutilit,
    }

    # Crea l'istanza del sincronizzatore
    syncer = DatabaseSynchronizer(
        duckdb_path=duckdb_path,
        pg_conn_string=pg_conn_string,
        schema="ctcn",
        tables=entity_types.keys(),
    )

    try:
        # Inizializza il sincronizzatore
        await syncer.initialize()

        # Esegui la sincronizzazione
        stats = await syncer.sync_database(entity_types)

        # Stampa le statistiche
        if stats.get("success"):
            print("Sincronizzazione fabbricati completata:")
            updated = stats["stats"]["updated"]
            inserted = stats["stats"]["inserted"]
            errors = stats["stats"]["errors"]
            print(f"    - Record aggiornati: {updated}")
            print(f"    - Record inseriti: {inserted}")
            print(f"    - Errori: {errors}")

    except Exception as e:
        print(f"Errore durante la sincronizzazione: {str(e)}")
        import traceback

        traceback.print_exc()
    finally:
        # Chiudi le connessioni
        await syncer.close()


if __name__ == "__main__":
    asyncio.run(sync_duckdb_to_postgres())
