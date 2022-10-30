from .common import CommonBase, CommonBaseRecord


class TerreniModel(CommonBase, CommonBaseRecord):
    pass


class TerreniRecord(TerreniModel):
    pass


class TerreniRecordUno(TerreniRecord):
    # Dati caratteristici della particella (terreno)
    qualita: str
    classe: str
    ettari: float
    are: float
    centiare: float
    # Dati relativi al reddito
    flag_reddito: str
    flag_porzione: str
    flag_deduzioni: str
    reddito_dominicale_lire: float
    reddito_agrario_lire: float
    reddito_dominicale_euro: float
    reddito_agrario_euro: float
    # Dati relativi all'atto che ha generato
    # la situazione oggettiva della particella
    data_di_efficacia00: str # TBD to_date
    data_di_registrazione00: str # TBD to_date
    tipo_nota00: str
    numero_nota00: str
    progressivo_nota00: str
    anno_nota00: str
    # Dati relativi all'atto che ha concluso
    # la situazione oggettiva della particella
    partita: str
    annotazione: str
    identificativo_mutazione_iniziale: str
    identificativo_mutazione_finale: str
    # Dati relativi all'atto che ha generato
    # la situazione oggettiva dell'unità
    codice_causale_atto_generante: str = None
    descrizione_atto_generante: str = None
    # Dati relativi all'atto che ha concluso
    # la situazione oggettiva dell'unità
    codice_causale_atto_conclusivo: str = None
    descrizione_atto_conclusivo: str = None


class TerreniRecordDue(TerreniRecord):
    simbolo_deduzione: str


class TerreniRecordTre(TerreniRecord):
    codice_riserva: str
    partita_iscrizione_riserva: str


class TerreniRecordQuattro(TerreniRecord):
    qualita: str
    classe: str
    ettari: str
    are: str
    centiare: str


class TerreniRecordQuattroModel(TerreniRecordQuattro):
    identificativo_porzione: str
