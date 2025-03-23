import asyncio

from catasto.postgres.db import DatabaseSynchronizer


# Esempio di utilizzo
async def sync_duckdb_to_postgres():
    """Funzione principale per la sincronizzazione da DuckDB a PostgreSQL."""
    from catasto.schemas.catastodb.models import (
        Cuarcuiu,
        Cuidenti,
        Cuindiri,
        Curiserv,
        Cuutilit,
    )

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
        duckdb_path=duckdb_path, pg_conn_string=pg_conn_string
    )

    try:
        # Inizializza il sincronizzatore
        await syncer.initialize()

        # Esegui la sincronizzazione
        stats = await syncer.sync_database(entity_types)

        breakpoint()
        # Stampa le statistiche
        if stats.get("success"):
            print("Sincronizzazione completata:")
            print(f"  - Record aggiornati: {stats["stats"]["updated"]}")
            print(f"  - Record inseriti: {stats["stats"]["inserted"]}")
            print(f"  - Errori: {stats["stats"]["errors"]}")

    except Exception as e:
        print(f"Errore durante la sincronizzazione: {str(e)}")
        import traceback

        traceback.print_exc()
    finally:
        # Chiudi le connessioni
        await syncer.close()


if __name__ == "__main__":
    asyncio.run(sync_duckdb_to_postgres())
