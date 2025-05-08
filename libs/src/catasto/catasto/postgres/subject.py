from typing import Any, Dict, Type

from pydantic import BaseModel


async def update_soggetti(
    syncer, entity_types: Dict[str, Type[BaseModel]]
) -> Dict[str, Any]:
    """
    Aggiorna le tabelle relative ai soggetti.

    Args:
        syncer: Un'istanza di DatabaseSynchronizer
        entity_types: Dizionario che mappa nomi di tabelle a tipi di entità Pydantic
    """

    logger = syncer.logger.bind(operation="update_soggetti")
    # Inizia una transazione nel database PostgreSQL
    transaction = None
    try:
        # Inizia la transazione
        transaction = syncer.pg_dal.begin_transaction()
        logger.info("transaction_started")

        # Esegui la sincronizzazione
        # Prima sincronizza la tabella ctfisica con la logica di update
        if "ctfisica" in syncer.tables and "ctfisica" in entity_types:
            await syncer._sync_ctfisica_with_update(entity_types["ctfisica"])

        # Poi sincronizza la tabella ctnonfis con la logica di update
        elif "ctnonfis" in syncer.tables and "ctnonfis" in entity_types:
            await syncer._sync_ctnonfis_with_update(entity_types["ctnonfis"])

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
