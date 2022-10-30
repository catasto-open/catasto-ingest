from pydantic import BaseModel
from .common import (
    CommonBase, CommonBaseRecord, CommonBaseParcel
)


class FabbricatiModel(CommonBase, CommonBaseRecord):
    pass


class FabbricatiRecordBase(BaseModel):
    id_immobile: str


class FabbricatiRecord(FabbricatiModel):
    zona: str
    categoria: str
    classe: str
    consistenza: float
    superficie: float
    rendita_lire: float
    rendita_euro: float


class FabbricatiRecordUno(FabbricatiRecord):
    # Dati relativi all'ubicazione dell'immobile
    # nel fabbricato
    lotto: str
    edificio: str
    scala: str
    interno1: str
    interno2: str
    piano1: str
    piano2: str
    piano3: str
    piano4: str
    # Dati relativi all'atto che ha generato
    # la situazione oggettiva dell'unità
    data_di_efficacia00: str # TBD to_date
    data_di_registrazione00: str # TBD to_date
    tipo_nota00: str
    numero_nota00: str
    progressivo_nota00: str
    anno_nota00: str
    data_di_efficacia99: str # TBD to_date
    data_di_registrazione99: str # TBD to_date
    tipo_nota99: str
    numero_nota99: str
    progressivo_nota99: str
    anno_nota99: str
    partita: str
    annotazione: str # handle accents
    identificativo_mutazione_iniziale: str
    identificativo_mutazione_finale: str
    protocollo_notifica: str
    data_notifica: str # TBD to_date
    # Dati aggiunti dal 2007
    # Dati relativi all'atto che ha generato
    # la situazione oggettiva dell'unità
    codice_causale_atto_generante: str = None
    descrizione_atto_generante: str = None
    # Dati relativi all'atto che ha concluso
    # la situazione oggettiva dell'unità
    codice_causale_atto_conclusivo: str = None
    descrizione_atto_conclusivo: str = None
    flag_classamento: str = None


class FabbricatiRecordUnoModel(
    FabbricatiRecordBase, FabbricatiRecordUno
):
    pass


class FabbricatiRecordDue(FabbricatiRecord, CommonBaseParcel):
    sezione_urbana: str
    id_particella: str


class FabbricatiRecordDueModel(
    FabbricatiRecordBase, FabbricatiRecordDue
):
    pass


class FabbricatiRecordDueCross(FabbricatiRecordDueModel):
    terreno_id: str


class FabbricatiRecordTre(FabbricatiRecord):
    toponimo: str
    indirizzo: str
    civico1: str
    civico2: str
    civico3: str
    codice_strada: str


class FabbricatiRecordTreModel(
    FabbricatiRecordBase, FabbricatiRecordTre
):
    pass


class FabbricatiRecordQuattro(FabbricatiRecord):
    sezione_urbana: str
    foglio: str
    numero: str
    denominatore:str
    subalterno: str


class FabbricatiRecordQuattroModel(
    FabbricatiRecordBase, FabbricatiRecordQuattro
):
    pass


class FabbricatiRecordCinque(FabbricatiRecord):
    codice_riserva: str
    partita_iscrizione_riserva: str


class FabbricatiRecordCinqueModel(
    FabbricatiRecordBase, FabbricatiRecordCinque
):
    pass


class FabbricatiTerreniModel(BaseModel):
    pass
