from typing import Any, Dict, Type

from pydantic import BaseModel


async def update_fabbricati(
    syncer, entity_types: Dict[str, Type[BaseModel]]
) -> Dict[str, Any]:
    """
    Aggiorna le tabelle relative ai fabbricati.

    Args:
        syncer: Un'istanza di DatabaseSynchronizer
        entity_types: Dizionario che mappa nomi di tabelle a tipi di entità Pydantic
    """

    logger = syncer.logger.bind(operation="update_fabbricati")
    # Inizia una transazione nel database PostgreSQL
    transaction = None
    try:
        # Inizia la transazione
        transaction = syncer.pg_dal.begin_transaction()
        logger.info("transaction_started")

        # Esegui la sincronizzazione
        # Prima sincronizza la tabella cuarcuiu con la logica di mutazione
        if "cuarcuiu" in syncer.tables and "cuarcuiu" in entity_types:
            await syncer._sync_cuarcuiu_with_mutation(entity_types["cuarcuiu"])

        # Poi sincronizza le altre tabelle
        for table in [
            t for t in syncer.tables if t != "cuarcuiu" and t in entity_types
        ]:
            await syncer._sync_related_table(table, entity_types[table])

        # Commit della transazione
        transaction.commit()
        logger.info("transaction_committed", stats=syncer.stats)

        return {"success": True, "stats": syncer.stats}

    except Exception as e:
        # Rollback in caso di errore
        if transaction:
            transaction.rollback()
            logger.error("transaction_rolled_back_due_to_error", error=str(e))

        syncer.stats["errors"] += 1
        logger.exception("sync_failed", error=str(e))

        return {"success": False, "reason": "sync_error", "error": str(e)}
