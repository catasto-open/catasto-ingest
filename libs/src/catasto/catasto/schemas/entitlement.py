from .common import (
    CommonBase, CommonBaseSubject, CommonBaseBuilding
)


class Titolarita(
    CommonBase, CommonBaseSubject, CommonBaseBuilding
):
    # Dati della titolarità
    codice_diritto: str
    titolo_non_codificato: str # handle accents
    quota_numeratore: str
    quota_denominatore: str
    regime: str
    soggetto_di_riferimento: str
    # Dati relativi all'atto che
    # ha generato la titolarità
    data_di_validita00: str # TBD to_date
    tipo_nota00: str
    numero_nota00: str
    progressivo_nota00: str
    anno_nota00: str
    data_registrazione_atti00: str # TBD to_date
    partita: str
    # Dati relativi all'atto che ha concluso
    # la situazione oggettiva dell'unità
    data_di_validita99: str # TBD to_date
    tipo_nota99: str
    numero_nota99: str
    progressivo_nota99: str
    anno_nota99: str
    data_registrazione_atti99: str # TBD to_date
    identificativo_mutazione_iniziale: str
    identificativo_mutazione_finale: str
    # Campo introdotto solo dal 2001
    identificativo_titolarita: str = None
    # Campi introdotti dal 2007
    codice_causale_atto_generante: str = None
    descrizione_atto_generante: str = None
    codice_causale_atto_conclusivo: str = None
    descrizione_atto_conclusivo: str = None


class TitolaritaModel(Titolarita):
    id_titolarita: str
