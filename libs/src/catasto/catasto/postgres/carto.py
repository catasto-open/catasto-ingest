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


async def update_particelle(
    syncer, entity_types: Dict[str, Type[BaseModel]]
) -> Dict[str, Any]:
    """
    Aggiorna le tabelle relative alle particelle.

    Args:
        syncer: Un'istanza di DatabaseSynchronizer
        entity_types: Dizionario che mappa nomi di tabelle a tipi di entità Pydantic
    """

    logger = syncer.logger.bind(operation="update_particelle")
    # Inizia una transazione nel database PostgreSQL
    transaction = None
    try:
        # Inizia la transazione
        transaction = syncer.pg_dal.begin_transaction()
        logger.info("transaction_started")

        # Esegui la sincronizzazione
        # Prima sincronizza la tabella particelle con la logica di delete-then-insert
        if "particelle" in syncer.tables and "particelle" in entity_types:
            await syncer._sync_particelle_with_delete(entity_types["particelle"])

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


async def update_fabbricati(
    syncer, entity_types: Dict[str, Type[BaseModel]]
) -> Dict[str, Any]:
    """
    Aggiorna le tabelle relative alle fabbricati.

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
        # Prima sincronizza la tabella fabbricati con la logica di delete-then-insert
        if "fabbricati" in syncer.tables and "fabbricati" in entity_types:
            await syncer._sync_fabbricati_with_delete(entity_types["fabbricati"])

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


async def update_quadri(
    syncer, entity_types: Dict[str, Type[BaseModel]]
) -> Dict[str, Any]:
    """
    Aggiorna le tabelle relative ai quadri d'unione.

    Args:
        syncer: Un'istanza di DatabaseSynchronizer
        entity_types: Dizionario che mappa nomi di tabelle a tipi di entità Pydantic
    """

    logger = syncer.logger.bind(operation="update_quadri")
    # Inizia una transazione nel database PostgreSQL
    transaction = None
    try:
        # Inizia la transazione
        transaction = syncer.pg_dal.begin_transaction()
        logger.info("transaction_started")

        # Esegui la sincronizzazione
        # Prima sincronizza la tabella quadri con la logica di delete-then-insert
        if "quadri_unione" in syncer.tables and "quadri" in entity_types:
            await syncer._sync_quadri_with_delete(entity_types["quadri"])

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


async def update_acque(
    syncer, entity_types: Dict[str, Type[BaseModel]]
) -> Dict[str, Any]:
    """
    Aggiorna le tabelle relative alle acque.

    Args:
        syncer: Un'istanza di DatabaseSynchronizer
        entity_types: Dizionario che mappa nomi di tabelle a tipi di entità Pydantic
    """

    logger = syncer.logger.bind(operation="update_acque")
    # Inizia una transazione nel database PostgreSQL
    transaction = None
    try:
        # Inizia la transazione
        transaction = syncer.pg_dal.begin_transaction()
        logger.info("transaction_started")

        # Esegui la sincronizzazione
        # Prima sincronizza la tabella acque con la logica di delete-then-insert
        if "acque" in syncer.tables and "acque" in entity_types:
            await syncer._sync_acque_with_delete(entity_types["acque"])

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


async def update_strade(
    syncer, entity_types: Dict[str, Type[BaseModel]]
) -> Dict[str, Any]:
    """
    Aggiorna le tabelle relative alle strade.

    Args:
        syncer: Un'istanza di DatabaseSynchronizer
        entity_types: Dizionario che mappa nomi di tabelle a tipi di entità Pydantic
    """

    logger = syncer.logger.bind(operation="update_strade")
    # Inizia una transazione nel database PostgreSQL
    transaction = None
    try:
        # Inizia la transazione
        transaction = syncer.pg_dal.begin_transaction()
        logger.info("transaction_started")

        # Esegui la sincronizzazione
        # Prima sincronizza la tabella strade con la logica di delete-then-insert
        if "strade" in syncer.tables and "strade" in entity_types:
            await syncer._sync_strade_with_delete(entity_types["strade"])

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


async def update_testi(
    syncer, entity_types: Dict[str, Type[BaseModel]]
) -> Dict[str, Any]:
    """
    Aggiorna le tabelle relative ai testi.

    Args:
        syncer: Un'istanza di DatabaseSynchronizer
        entity_types: Dizionario che mappa nomi di tabelle a tipi di entità Pydantic
    """

    logger = syncer.logger.bind(operation="update_testi")
    # Inizia una transazione nel database PostgreSQL
    transaction = None
    try:
        # Inizia la transazione
        transaction = syncer.pg_dal.begin_transaction()
        logger.info("transaction_started")

        # Esegui la sincronizzazione
        # Prima sincronizza la tabella testi con la logica di delete-then-insert
        if "testi" in syncer.tables and "testi" in entity_types:
            await syncer._sync_testi_with_delete(entity_types["testi"])

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


async def update_simboli(
    syncer, entity_types: Dict[str, Type[BaseModel]]
) -> Dict[str, Any]:
    """
    Aggiorna le tabelle relative ai simboli.

    Args:
        syncer: Un'istanza di DatabaseSynchronizer
        entity_types: Dizionario che mappa nomi di tabelle a tipi di entità Pydantic
    """

    logger = syncer.logger.bind(operation="update_simboli")
    # Inizia una transazione nel database PostgreSQL
    transaction = None
    try:
        # Inizia la transazione
        transaction = syncer.pg_dal.begin_transaction()
        logger.info("transaction_started")

        # Esegui la sincronizzazione
        # Prima sincronizza la tabella simboli con la logica di delete-then-insert
        if "simboli" in syncer.tables and "simboli" in entity_types:
            await syncer._sync_simboli_with_delete(entity_types["simboli"])

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
