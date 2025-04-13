from typing import Any, Dict, Type

from pydantic import BaseModel


async def update_fogli(
    syncer, entity_types: Dict[str, Type[BaseModel]]
) -> Dict[str, Any]:
    """
    Aggiorna le tabelle relative ai fogli.

    Args:
        syncer: Un'istanza di DatabaseSynchronizer
        entity_types: Dizionario che mappa nomi di tabelle a tipi di entità Pydantic
    """

    logger = syncer.logger.bind(operation="update_fogli")
    # Inizia una transazione nel database PostgreSQL
    transaction = None
    try:
        # Inizia la transazione
        transaction = syncer.pg_dal.begin_transaction()
        logger.info("transaction_started")

        # Esegui la sincronizzazione
        # Prima sincronizza la tabella fogli con la logica di delete-then-insert
        if "fogli" in syncer.tables and "fogli" in entity_types:
            await syncer._sync_fogli_with_delete(entity_types["fogli"])

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
