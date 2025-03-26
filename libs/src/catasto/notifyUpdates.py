import asyncio
import json
from datetime import datetime
import duckdb
import nats


async def publish_record(js, duck_conn, record):
    try:
        dt = datetime.strptime(record['data_modifica'], '%d%m%Y')
        tipo_immobile = record['tipo_immobile']
        payload = {
            "identificativo_immobile": int(record['codice_immobile']),
            "data_aggiornamento": dt.isoformat(),
            "tipo_immobile": tipo_immobile,
            "identificativo_operazione": record['tipo_operazione'].upper() if record['tipo_operazione'] else None
        }
        json_payload = json.dumps(payload).encode()
        ack = await js.publish("CATASTO.changed", json_payload)

        # Update sent_on timestamp
        sent_on = datetime.utcnow().isoformat()
        duck_conn.execute(
            """
            UPDATE ctcn.to_notify_ancillary
            SET sent_on = ?
            WHERE codice_immobile = ? AND tipo_immobile = ? AND data_modifica = ?
            """,
            [sent_on, record['codice_immobile'], record['tipo_immobile'], record['data_modifica']]
        )

        print(f"Messaggio inviato per identificativo_immobile {payload['identificativo_immobile']}: {ack}")
    except Exception as e:
        print(f"Errore nell'invio del record {record}: {e}")


async def push_from_duckdb_to_nats(duckdb_filepath, nats_endpoint):
    """
    Invia gli identificativi aggiornati al NATS
    Quando viene lanciato la tabella to_notify_ancillary deve essere già stata popolata in duckdb_filepath

    Args:
        duckdb_filepath: Percorso al file DuckDB
        nats_endpoint: Connessione al db postgres con i dati del catasto (tipo nats://localhost:4222)

    """
    nc = await nats.connect(nats_endpoint)
    try:
        js = nc.jetstream()
        await js.add_stream(name="CATASTO", subjects=["CATASTO.changed"])

        tasks = []
        with duckdb.connect(duckdb_filepath) as duck_conn:
            duck_conn.execute("ALTER TABLE ctcn.to_notify_ancillary ADD COLUMN IF NOT EXISTS sent_on TIMESTAMP")

            rows = duck_conn.execute("SELECT codice_immobile, tipo_immobile, data_modifica, tipo_operazione FROM ctcn.to_notify_ancillary WHERE sent_on IS NULL").fetchdf()

            for _, row in rows.iterrows():
                record = {
                    'codice_immobile': row['codice_immobile'],
                    'tipo_immobile': row['tipo_immobile'],
                    'data_modifica': row['data_modifica'],
                    'tipo_operazione': row['tipo_operazione']
                }
                tasks.append(publish_record(js, duck_conn, record))

            await asyncio.gather(*tasks)

    finally:
        await nc.close()
