import time
from pathlib import Path

import duckdb
import structlog
from osgeo.ogr import Geometry, wkbLinearRing, wkbPoint, wkbPolygon
from pydantic import ValidationError
from structlog.stdlib import BoundLogger

from catasto.carto import transform_vertices
from catasto.coords import detect_crs_from_cxf, transform_cxf_vertices
from catasto.duckdb.repository import DuckDBRepository
from catasto.parser import FileParserService
from catasto.reader import LocalFileReaderService
from catasto.schemas.carto import CartoBordo, CartoObjectItem
from catasto.schemas.catastodb.models import Fabbricati, Fogli, Quadri


async def load_carto(
    cxf_filepath: str,
    duckdb_filepath: str,
    clean_tables: bool,
    logger: BoundLogger = None,
) -> str:
    """
    Carica i dati del cartografico da un file .Cxf in un database DuckDB.

    Args:
        cxf_filepath: Percorso al file .Cxf
        duckdb_filepath: Percorso al file DuckDB
        clean_tables: Se True, cancella i dati esistenti nelle tabelle
        logger: Logger strutturato da utilizzare (se None, ne viene creato uno)

    Returns:
        str: Percorso al database DuckDB
    """
    # Crea un logger predefinito se non fornito
    if logger is None:
        logger = structlog.get_logger("catasto.duckdb.carto")
    start_time = time.time()
    logger.info(
        "load_started",
        input_file=cxf_filepath,
        database=duckdb_filepath,
        clean_tables=clean_tables,
    )

    # Verifiche preliminari
    file_path = Path(cxf_filepath)
    db_path = Path(duckdb_filepath)

    if not file_path.exists():
        logger.error(f"File {cxf_filepath} non trovato")
        raise FileNotFoundError(f"File {cxf_filepath} non trovato.")

    if db_path.exists():
        logger.error(f"File {duckdb_filepath} già esistente")

    # Crea una connessione diretta a DuckDB per inizializzare il database
    logger.debug(f"Connessione al database DuckDB {duckdb_filepath}")
    duck_conn = duckdb.connect(duckdb_filepath)

    try:
        # Crea lo schema se non esiste
        logger.debug("Creazione dello schema ctmp")
        duck_conn.execute("CREATE SCHEMA IF NOT EXISTS ctmp")
        # Installa l'estensione spaziale
        logger.debug("Installazione dell'estensione spaziale")
        duck_conn.execute("INSTALL spatial;")
        duck_conn.execute("LOAD spatial;")
        # Crea tutte le tabelle direttamente in DuckDB
        logger.debug("Creazione della tabella fogli")
        duck_conn.execute("""
        CREATE TABLE IF NOT EXISTS ctmp.fogli (
            comune varchar(4) NOT NULL,
            sezione varchar(1) NOT NULL,
            foglio varchar(4) NOT NULL,
            allegato varchar(1) NULL,
            sviluppo varchar(1) NULL,
            t_altezza numeric(12, 2) NULL,
            t_angolo numeric(12, 2) NULL,
            t_pt_ins public.geometry NULL,
            t_ln_anc public.geometry NULL,
            geom public.geometry NOT NULL
        )
        """)

        logger.debug("Creazione della tabella particelle")
        duck_conn.execute("""
        CREATE TABLE IF NOT EXISTS ctmp.particelle (
            comune varchar(4) NOT NULL,
            sezione varchar(1) NOT NULL,
            foglio varchar(4) NOT NULL,
            allegato varchar(1) NULL,
            sviluppo varchar(1) NULL,
            numero varchar(9) NULL,
            t_altezza numeric(12, 2) NULL,
            t_angolo numeric(12, 2) NULL,
            t_pt_ins public.geometry NULL,
            t_ln_anc public.geometry NULL,
            geom public.geometry NOT NULL
        )
        """)

        logger.debug("Creazione della tabella acque")
        duck_conn.execute("""
        CREATE TABLE IF NOT EXISTS ctmp.acque (
            comune varchar(4) NOT NULL,
            sezione varchar(1) NOT NULL,
            foglio varchar(4) NOT NULL,
            allegato varchar(1) NULL,
            sviluppo varchar(1) NULL,
            numero varchar(9) NULL,
            t_altezza numeric(12, 2) NULL,
            t_angolo numeric(12, 2) NULL,
            t_pt_ins public.geometry NULL,
            t_ln_anc public.geometry NULL,
            geom public.geometry NOT NULL
        )
        """)

        logger.debug("Creazione della tabella fiduciali")
        duck_conn.execute("""
        CREATE TABLE IF NOT EXISTS ctmp.fiduciali (
            comune varchar(4) NOT NULL,
            sezione varchar(1) NOT NULL,
            foglio varchar(4) NOT NULL,
            allegato varchar(1) NULL,
            sviluppo varchar(1) NULL,
            prog int4 NOT NULL,
            codice int4 NOT NULL,
            esterno int4 NOT NULL,
            t_pt_ins public.geometry NULL,
            geom public.geometry NOT NULL
        )
        """)

        logger.debug("Creazione della tabella fabbricati")
        duck_conn.execute("""
        CREATE TABLE IF NOT EXISTS ctmp.fabbricati (
            comune varchar(4) NOT NULL,
            sezione varchar(1) NOT NULL,
            foglio varchar(4) NOT NULL,
            allegato varchar(1) NULL,
            sviluppo varchar(1) NULL,
            numero varchar(9) NULL,
            t_altezza numeric(12, 2) NULL,
            t_angolo numeric(12, 2) NULL,
            t_pt_ins public.geometry NULL,
            t_ln_anc public.geometry NULL,
            geom public.geometry NOT NULL
        )
        """)

        logger.debug("Creazione della tabella libretti")
        duck_conn.execute("""
        CREATE TABLE IF NOT EXISTS ctmp.libretti (
            comune varchar(4) NOT NULL,
            sezione varchar(1) NOT NULL,
            foglio varchar(4) NOT NULL,
            allegato varchar(1) NULL,
            sviluppo varchar(1) NULL,
            protocollo varchar(80) NULL,
            codice int4 NOT NULL,
            geom public.geometry NOT NULL
        )
        """)

        logger.debug("Creazione della tabella linee_vest")
        duck_conn.execute("""
        CREATE TABLE IF NOT EXISTS ctmp.linee_vest (
            comune varchar(4) NOT NULL,
            sezione varchar(1) NOT NULL,
            foglio varchar(4) NOT NULL,
            allegato varchar(1) NULL,
            sviluppo varchar(1) NULL,
            codice int4 NOT NULL,
            esterno int4 NOT NULL
        )
        """)

        logger.debug("Creazione della tabella quadri_unione")
        duck_conn.execute("""
        CREATE TABLE IF NOT EXISTS ctmp.quadri_unione (
            comune varchar(4) NOT NULL,
            sezione varchar(1) NOT NULL,
            foglio varchar(4) NOT NULL,
            allegato varchar(1) NULL,
            sviluppo varchar(1) NULL,
            t_altezza numeric(12, 2) NULL,
            t_angolo numeric(12, 2) NULL,
            t_pt_ins public.geometry NULL,
            t_ln_anc public.geometry NULL,
            geom public.geometry NOT NULL
        )
        """)

        logger.debug("Creazione della tabella simboli")
        duck_conn.execute("""
        CREATE TABLE IF NOT EXISTS ctmp.simboli (
            comune varchar(4) NOT NULL,
            sezione varchar(1) NOT NULL,
            foglio varchar(4) NOT NULL,
            allegato varchar(1) NULL,
            sviluppo varchar(1) NULL,
            codice int4 NOT NULL,
            angolo numeric(12, 2) NULL,
            esterno int4 NOT NULL,
            geom public.geometry NOT NULL
        )
        """)

        logger.debug("Creazione della tabella strade")
        duck_conn.execute("""
        CREATE TABLE IF NOT EXISTS ctmp.strade (
            comune varchar(4) NOT NULL,
            sezione varchar(1) NOT NULL,
            foglio varchar(4) NOT NULL,
            allegato varchar(1) NULL,
            sviluppo varchar(1) NULL,
            numero varchar(9) NULL,
            t_altezza numeric(12, 2) NULL,
            t_angolo numeric(12, 2) NULL,
            t_pt_ins public.geometry NULL,
            t_ln_anc public.geometry NULL,
            geom public.geometry NOT NULL
        )
        """)

        logger.debug("Creazione della tabella testi")
        duck_conn.execute("""
        CREATE TABLE IF NOT EXISTS ctmp.testi (
            comune varchar(4) NOT NULL,
            sezione varchar(1) NOT NULL,
            foglio varchar(4) NOT NULL,
            allegato varchar(1) NULL,
            sviluppo varchar(1) NULL,
            testo varchar(80) NULL,
            altezza numeric(12, 2) NULL,
            angolo numeric(12, 2) NULL,
            esterno int4 NOT NULL,
            geom public.geometry NOT NULL
        )
        """)

        # Se richiesto, pulisci le tabelle
        if clean_tables:
            logger.info("Pulizia delle tabelle richiesta")
            for table in [
                "fogli",
                "particelle",
                "acque",
                "fiduciali",
                "fabbricati",
                "libretti",
                "linee_vest",
                "quadri_unione",
                "simboli",
                "strade",
                "testi",
            ]:
                duck_conn.execute(f"DELETE FROM ctmp.{table}")
            logger.info("Tabelle svuotate con successo")

        # Crea repository manuali senza dipendere dal DAL
        logger.debug("Inizializzazione dei repository")
        fogli_repo = DuckDBRepository(
            connection=duck_conn,
            entity_type=Fogli,
            table_name="ctmp.fogli",
            primary_keys=["comune", "sezione", "foglio", "allegato", "sviluppo"],
        )
        quadri_repo = DuckDBRepository(
            connection=duck_conn,
            entity_type=Quadri,
            table_name="ctmp.quadri_unione",
            primary_keys=[
                "comune",
                "sezione",
                "foglio",
                "allegato",
                "sviluppo",
            ],
        )
        fabbricati_repo = DuckDBRepository(
            connection=duck_conn,
            entity_type=Fabbricati,
            table_name="ctmp.fabbricati",
            primary_keys=[
                "comune",
                "sezione",
                "foglio",
                "allegato",
                "sviluppo",
                "numero",
            ],
        )

        # Verifica quanti record ci sono nelle tabelle
        count_before = duck_conn.execute("SELECT COUNT(*) FROM ctmp.fogli").fetchone()[
            0
        ]
        logger.info(
            f"Record esistenti nella tabella fogli prima dell'inserimento: {count_before}"
        )

        # Recupera tutti i dati dal file
        logger.info(f"Parsing del file {cxf_filepath}")
        reader = LocalFileReaderService(filepath=cxf_filepath)
        parser = FileParserService(reader=reader)
        content = await parser.parse()

        # Processo di elaborazione
        async def process_bordi():
            # Raccogli tutti i record
            fogli_records = []
            quadri_records = []
            fabbricati_records = []
            particelle_records = []
            strade_records = []
            acque_records = []

            if content.oggetti.bordo:
                logger.debug(
                    f"Parsing completato, numero di bordi: {len(content.oggetti.bordo)}"
                )
                for bordo_item in content.oggetti.bordo:
                    # foglio
                    foglio = CartoObjectItem(
                        comune=content.codice_comune,
                        sezione=content.codice_sezione_censuaria,
                        foglio=content.codice_numero_foglio,
                        allegato=content.codice_allegato,
                        sviluppo=content.codice_sviluppo,
                    )
                    bordo = CartoBordo(**foglio.model_dump(), **bordo_item)
                    crs = detect_crs_from_cxf(vertices=bordo.vertici, mun_code="H501")
                    if crs == "cassini-soldner":
                        t_vertices = transform_cxf_vertices(
                            vertices=bordo.vertici,
                            source_crs="cassini-soldner",
                            target_crs="gauss-boaga-east",
                            mun_code="H501",
                        )
                        bordo.vertici = t_vertices
                    elif crs == "gauss-boaga-west":
                        t_vertices = transform_cxf_vertices(
                            vertices=bordo.vertici,
                            source_crs="gauss-boaga-west",
                            target_crs="gauss-boaga-east",
                            mun_code="H501",
                        )
                        bordo.vertici = t_vertices
                    elif crs == "gauss-boaga-east":
                        logger.info("Skip coordinates transformation")
                        pass
                    try:
                        polygon = Geometry(wkbPolygon)
                        tabisole = list(map(int, bordo.tabisole))
                        # outer boundary
                        vertexes = int(bordo.numerovertici) - sum(tabisole)
                        ring = Geometry(wkbLinearRing)
                        for vertex in range(vertexes):
                            x, y = map(float, bordo.vertici[vertex])
                            ring.AddPoint(x, y)
                        ring.CloseRings()
                        polygon.AddGeometry(ring)
                        # islands
                        for island in range(int(bordo.numeroisole)):
                            ring = Geometry(wkbLinearRing)
                            for vertex in range(
                                vertex + 1, vertex + 1 + tabisole[island]
                            ):
                                x, y = map(float, bordo.vertici[vertex])
                                ring.AddPoint(x, y)
                            ring.CloseRings()
                            polygon.AddGeometry(ring)
                        polygon.FlattenTo2D()
                        bordo.geometry = polygon.ExportToWkt()
                        if bordo.posizione_x and bordo.posizione_y:
                            t_pt_ins = Geometry(wkbPoint)
                            t_pt_ins_x, t_pt_ins_y = map(
                                float,
                                transform_vertices(
                                    vertices=[(bordo.posizione_x, bordo.posizione_y)],
                                    mun_code="H501",
                                )[0],
                            )
                            t_pt_ins.AddPoint(t_pt_ins_x, t_pt_ins_y)
                            t_pt_ins.FlattenTo2D()
                            bordo.t_pt_ins = t_pt_ins.ExportToWkt()
                        if bordo.puntointerno_x and bordo.puntointerno_y:
                            t_ln_anc = Geometry(wkbPoint)
                            t_ln_anc_x, t_ln_anc_y = map(
                                float,
                                transform_vertices(
                                    vertices=[
                                        (bordo.puntointerno_x, bordo.puntointerno_y)
                                    ],
                                    mun_code="H501",
                                )[0],
                            )
                            t_ln_anc.AddPoint(t_ln_anc_x, t_ln_anc_y)
                            t_ln_anc.FlattenTo2D()
                            bordo.t_ln_anc = t_ln_anc.ExportToWkt()
                    except ValidationError:
                        logger.error(f"Error validating geometry: {polygon}")
                    if bordo.tipo == "CONFINE":
                        if bordo.codice_identificativo == content.codice_foglio:
                            fogli_records.append(
                                Fogli.extract_from_model(dati_foglio=bordo)
                            )
                        else:
                            if len(bordo.codice_identificativo):
                                quadri_records.append(
                                    Quadri.extract_from_model(dati_quadro_unione=bordo)
                                )
                    elif bordo.tipo == "STRADA":
                        strade_records.append(bordo)
                    elif bordo.tipo == "ACQUA":
                        acque_records.append(bordo)
                    elif bordo.tipo == "FABBRICATO":
                        bordo.codice_identificativo = bordo.codice_identificativo[:-1]
                        fabbricati_records.append(
                            Fabbricati.extract_from_model(dati_fabbricato=bordo)
                        )
                    elif bordo.tipo == "PARTICELLA":
                        particelle_records.append(bordo)
                    else:
                        logger.error(f"Tipo {bordo.tipo} non implementato")
                        pass

            if content.oggetti.fiduciale:
                logger.debug(
                    f"Parsing completato, numero di bordi: {len(content.oggetti.fiduciale)}"
                )
            if content.oggetti.linea:
                logger.debug(
                    f"Parsing completato, numero di bordi: {len(content.oggetti.linea)}"
                )
            if content.oggetti.simbolo:
                logger.debug(
                    f"Parsing completato, numero di bordi: {len(content.oggetti.simbolo)}"
                )
            if content.oggetti.testo:
                logger.debug(
                    f"Parsing completato, numero di bordi: {len(content.oggetti.testo)}"
                )

            logger.info(
                f"Record estratti: fogli={len(fogli_records)}, quadri={len(quadri_records)}, "
                f"fabbricati={len(fabbricati_records)}, particelle={len(particelle_records)}, "
                f"acque={len(acque_records)}, strade={len(strade_records)}"
            )

            # Inserisci tutti i record
            total_records = 0

            insert_start_time = time.time()

            if fogli_records:
                logger.info(f"Inserimento di {len(fogli_records)} record in fogli")
                count = await fogli_repo.insert_many(fogli_records)
                logger.info(f"Inseriti {count} record in fogli")
                total_records += count
            if quadri_records:
                logger.info(
                    f"Inserimento di {len(quadri_records)} record in quadri unione"
                )
                count = await quadri_repo.insert_many(quadri_records)
                logger.info(f"Inseriti {count} record in quadri unione")
                total_records += count
            if fabbricati_records:
                logger.info(
                    f"Inserimento di {len(fabbricati_records)} record in fabbricati"
                )
                count = await fabbricati_repo.insert_many(fabbricati_records)
                logger.info(f"Inseriti {count} record in fabbricati")
                total_records += count

            insert_duration = time.time() - insert_start_time
            logger.info(f"Inserimento completato in {insert_duration:.2f} secondi")
            return total_records

        # Esegui il processo
        result_bordi = await process_bordi()
        logger.info(f"Inseriti in totale {result_bordi} record bordi")

        # Verifica i dati inseriti
        tables = [
            "fogli",
            "quadri_unione",
            "particelle",
            "fabbricati",
            "acque",
            "strade",
        ]
        for table in tables:
            count = duck_conn.execute(f"SELECT COUNT(*) FROM ctmp.{table}").fetchone()[
                0
            ]
            logger.info(f"Totale record in {table}: {count}")

        # Mostra alcuni esempi (solo nel log di livello debug)
        logger.debug("Esempi di dati in particelle:")
        sample = duck_conn.execute("SELECT * FROM ctmp.particelle LIMIT 3").fetchall()
        for idx, row in enumerate(sample):
            logger.debug(f"Row {idx+1}: {row}")

        duration = time.time() - start_time
        logger.info(f"Caricamento dati completato in {duration:.2f} secondi")
        return duckdb_filepath

    except Exception as e:
        logger.exception(f"Errore durante il caricamento: {str(e)}")
        raise
    finally:
        # Chiudi la connessione
        logger.debug("Chiusura della connessione al database")
        duck_conn.close()
