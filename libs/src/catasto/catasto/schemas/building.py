import re
from datetime import datetime
from typing import Annotated, List, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .common import CommonBase, CommonBaseRecord, OptionalStr


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


class BaseRecord(BaseModel):
    """Classe base per tutti i record del file fabbricati."""

    codice_amministrativo: Annotated[
        str, Field(min_length=4, max_length=4, alias="CODICE AMMINISTRATIVO")
    ]
    sezione: Annotated[OptionalStr, Field(min_length=1, max_length=1, alias="SEZIONE")]
    identificativo_immobile: Annotated[
        str, Field(max_length=15, alias="IDENTIFICATIVO IMMOBILE")
    ]
    tipo_immobile: Annotated[
        Literal["F"], Field(min_length=1, max_length=1, alias="TIPO IMMOBILE")
    ]  # Deve essere 'F' per i fabbricati
    progressivo: Annotated[str, Field(min_length=1, max_length=3, alias="PROGRESSIVO")]
    tipo_record: Annotated[
        str, Field(min_length=1, max_length=1, alias="TIPO RECORD")
    ]  # Sarà validato dalle sottoclassi

    model_config = ConfigDict(
        extra="forbid", populate_by_name=True
    )  # Non permettere campi non definiti

    @field_validator("codice_amministrativo")
    @classmethod
    def check_codice_belfiore(cls, v):
        if not (v[1:].isdigit() and len(v[1:]) == 3) or not (
            v[0].isalpha() and len(v[0]) == 1
        ):
            raise ValueError(
                "codice amministrativo deve essere in formato belfiore, es. H501"
            )
        return v

    @field_validator("progressivo")
    @classmethod
    def check_progressivo_numerico(cls, v):
        if not v.isdigit():
            raise ValueError("progressivo deve essere numerico")
        return v

    @field_validator("tipo_record")
    @classmethod
    def check_tipo_record_numerico(cls, v):
        if not v.isdigit():
            raise ValueError("tipo record deve essere numerico")
        return v


class FabbricatiRecord1(BaseRecord):
    """Record di tipo 1: caratteristiche dell'unità immobiliare."""

    tipo_record: Annotated[
        Literal["1"], Field(min_length=1, max_length=1, alias="TIPO RECORD")
    ]

    # Dati relativi al classamento
    zona: Annotated[str, Field(min_length=1, max_length=3, alias="ZONA")]
    categoria: Annotated[str, Field(min_length=1, max_length=3, alias="CATEGORIA")]
    classe: Annotated[str, Field(min_length=2, max_length=2, alias="CLASSE")]
    consistenza: Annotated[str, Field(min_length=1, max_length=7, alias="CONSISTENZA")]
    superficie: Annotated[str, Field(min_length=1, max_length=5, alias="SUPERFICIE")]
    rendita_lire: Annotated[
        OptionalStr,
        Field(default=None, min_length=0, max_length=15, alias="RENDITA-LIRE"),
    ]
    rendita_euro: Annotated[
        OptionalStr,
        Field(default=None, min_length=0, max_length=18, alias="RENDITA-EURO"),
    ]

    # Dati relativi all'ubicazione
    lotto: Annotated[
        str | None, Field(default=None, min_length=0, max_length=2, alias="LOTTO")
    ]
    edificio: Annotated[
        str | None, Field(default=None, min_length=0, max_length=2, alias="EDIFICIO")
    ]
    scala: Annotated[
        str | None, Field(default=None, min_length=0, max_length=2, alias="SCALA")
    ]
    interno1: Annotated[
        str | None, Field(default=None, min_length=0, max_length=3, alias="INTERNO 1")
    ]
    interno2: Annotated[
        str | None, Field(default=None, min_length=0, max_length=3, alias="INTERNO 2")
    ]
    piano1: Annotated[
        str | None, Field(default=None, min_length=0, max_length=4, alias="PIANO 1")
    ]
    piano2: Annotated[
        str | None, Field(default=None, min_length=0, max_length=4, alias="PIANO 2")
    ]
    piano3: Annotated[
        str | None, Field(default=None, min_length=0, max_length=4, alias="PIANO 3")
    ]
    piano4: Annotated[
        str | None, Field(default=None, min_length=0, max_length=4, alias="PIANO 4")
    ]

    # Dati relativi all'atto che ha generato la situazione oggettiva
    data_efficacia_iniziale: Annotated[
        str, Field(max_length=8, alias="DATA DI EFFICACIA")
    ]
    data_registrazione_atti_iniziale: Annotated[
        str, Field(min_length=0, max_length=8, alias="DATA DI REGISTRAZIONE IN ATTI")
    ]
    tipo_nota_iniziale: Annotated[
        str, Field(min_length=0, max_length=1, alias="TIPO NOTA")
    ]
    numero_nota_iniziale: Annotated[
        str, Field(min_length=0, max_length=6, alias="NUMERO NOTA")
    ]
    progressivo_nota_iniziale: Annotated[
        str, Field(min_length=0, max_length=3, alias="PROGRESSIVO NOTA")
    ]
    anno_nota_iniziale: Annotated[
        str, Field(min_length=4, max_length=4, alias="ANNO NOTA")
    ]

    # Dati relativi all'atto che ha concluso la situazione oggettiva
    data_efficacia_finale: Annotated[
        OptionalStr,
        Field(default=None, max_length=8, alias="DATA DI EFFICACIA"),
    ]
    data_registrazione_atti_finale: Annotated[
        OptionalStr,
        Field(
            default=None,
            max_length=8,
            alias="DATA DI REGISTRAZIONE IN ATTI",
        ),
    ]
    tipo_nota_finale: Annotated[
        OptionalStr, Field(default=None, max_length=1, alias="TIPO NOTA")
    ]
    numero_nota_finale: Annotated[
        OptionalStr,
        Field(default=None, max_length=6, alias="NUMERO NOTA"),
    ]
    progressivo_nota_finale: Annotated[
        OptionalStr,
        Field(default=None, max_length=3, alias="PROGRESSIVO NOTA"),
    ]
    anno_nota_finale: Annotated[
        OptionalStr, Field(default=None, max_length=4, alias="ANNO NOTA")
    ]

    # Altri campi
    partita: Annotated[OptionalStr, Field(default=None, max_length=7, alias="PARTITA")]
    annotazione: Annotated[
        OptionalStr, Field(default=None, max_length=200, alias="ANNOTAZIONE")
    ]
    identificativo_mutazione_iniziale: Annotated[
        OptionalStr,
        Field(
            default=None,
            max_length=9,
            alias="IDENTIFICATIVO MUTAZIONE INIZIALE",
        ),
    ]
    identificativo_mutazione_finale: Annotated[
        str | None,
        Field(
            default=None,
            max_length=9,
            alias="IDENTIFICATIVO MUTAZIONE FINALE",
        ),
    ]
    protocollo_notifica: Annotated[
        OptionalStr,
        Field(
            default=None,
            max_length=18,
            alias="PROTOCOLLO NOTIFICA",
        ),
    ]
    data_notifica: Annotated[
        OptionalStr,
        Field(
            default=None,
            max_length=8,
            alias="DATA NOTIFICA",
        ),
    ]
    codice_causale_atto_generante: Annotated[
        OptionalStr,
        Field(
            default=None,
            max_length=3,
            alias="CODICE CAUSALE ATTO GENERANTE",
        ),
    ]
    descrizione_atto_generante: Annotated[
        OptionalStr,
        Field(
            default=None,
            max_length=100,
            alias="DESCRIZIONE ATTO GENERANTE",
        ),
    ]
    codice_causale_atto_conclusivo: Annotated[
        OptionalStr,
        Field(
            default=None,
            max_length=3,
            alias="CODICE CAUSALE ATTO CONCLUSIVO",
        ),
    ]
    descrizione_atto_conclusivo: Annotated[
        OptionalStr,
        Field(
            default=None,
            max_length=100,
            alias="DESCRIZIONE ATTO CONCLUSIVO",
        ),
    ]
    flag_classamento: Annotated[
        str | None,
        Field(
            default=None,
            max_length=1,
            alias="FLAG CLASSAMENTO",
        ),
    ]

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    @field_validator(
        "data_efficacia_iniziale",
        "data_registrazione_atti_iniziale",
        "data_efficacia_finale",
        "data_registrazione_atti_finale",
        "data_notifica",
    )
    @classmethod
    def validate_date(cls, v):
        """Valida che il campo contenga una data nel formato GGMMAAAA."""
        if not v:
            return v

        # Verifica la lunghezza esatta
        if len(v) != 8:
            raise ValueError(f"La data deve avere esattamente 8 caratteri: {v}")

        # Verifica che siano tutti numeri
        if not v.isdigit():
            raise ValueError(f"La data deve contenere solo cifre numeriche: {v}")

        # Estrai giorno, mese e anno
        giorno, mese, anno = v[:2], v[2:4], v[4:]

        try:
            # Verifica che siano validi come numeri
            g, m, a = int(giorno), int(mese), int(anno)

            # Verifica intervalli validi
            if not (1 <= g <= 31):
                raise ValueError(f"Giorno non valido: {giorno}")
            if not (1 <= m <= 12):
                raise ValueError(f"Mese non valido: {mese}")
            if not (1900 <= a <= 2999):  # Intervallo ragionevole di anni
                raise ValueError(f"Anno non valido: {anno}")

            # Prova a creare un oggetto datetime per verificare la validità completa
            datetime(a, m, g)

            return v
        except ValueError as e:
            raise ValueError(f"Data non valida ({v}): {str(e)}")

    @field_validator("flag_classamento")
    @classmethod
    def validate_flag_classamento(cls, v):
        if v is None:
            return v
        valid_flags = ["1", "2", "3", "4", "5", " "]
        if v not in valid_flags:
            raise ValueError(
                f"Flag classamento non valido. Deve essere uno tra {valid_flags}"
            )
        return v

    @field_validator("categoria")
    @classmethod
    def validate_categoria(cls, v):
        # Verificare che la categoria sia valida secondo le specifiche del catasto
        if not re.match(r"^[ABC][0-9]{1,2}$", v):
            raise ValueError(
                "Categoria non valida. Deve iniziare con A, B o C seguito da numeri"
            )
        return v

    @field_validator("consistenza")
    @classmethod
    def validate_consistenza(cls, v, info):
        # Ottenere il valore del campo 'categoria' dai dati di input
        data = info.data
        categoria = data.get("categoria", "")
        if not categoria:
            return v

        # La consistenza dipende dalla prima lettera della categoria
        if categoria.startswith("A"):
            # Deve essere in vani (ultimo carattere 0 o 5)
            if v[-1] not in ["0", "5"]:
                raise ValueError(
                    "Per categorie A, l'ultimo carattere della consistenza deve essere 0 o 5"
                )
        elif categoria.startswith("B"):
            # Deve essere in metri cubi
            if not v.replace(".", "").isdigit():
                raise ValueError(
                    "Per categorie B, la consistenza deve essere numerica (metri cubi)"
                )
        elif categoria.startswith("C"):
            # Deve essere in metri quadrati
            if not v.replace(".", "").isdigit():
                raise ValueError(
                    "Per categorie C, la consistenza deve essere numerica (metri quadrati)"
                )
        return v

    @field_validator("rendita_euro")
    @classmethod
    def validate_rendita_euro(cls, v):
        # Gli ultimi 2 caratteri sono decimali
        # if not re.match(r"^\d+\.\d{2}$", v):
        if v:
            decimal = v.split(",")[1]
            if len(decimal) < 2:
                raise ValueError(
                    "Rendita Euro non valida. Gli ultimi 2 caratteri devono essere decimali"
                )
        return v

    @model_validator(mode="after")
    def check_date_relationships(self) -> "FabbricatiRecord1":
        """Verifica la coerenza tra le date."""
        # check data efficacia
        if self.data_efficacia_iniziale and self.data_efficacia_finale:
            if datetime.strptime(
                self.data_efficacia_iniziale, "%d%m%Y"
            ) > datetime.strptime(self.data_efficacia_finale, "%d%m%Y"):
                raise ValueError(
                    "La data di efficacia iniziale non può essere successiva alla data di efficacia finale"
                )
        # check data registrazione
        if (
            self.data_registrazione_atti_iniziale
            and self.data_registrazione_atti_finale
        ):
            if datetime.strptime(
                self.data_registrazione_atti_iniziale, "%d%m%Y"
            ) > datetime.strptime(self.data_registrazione_atti_finale, "%d%m%Y"):
                raise ValueError(
                    "La data di registrazione iniziale non può essere successiva alla data di registrazione finale"
                )

        return self


class Identificativo(BaseModel):
    """Modello per un singolo identificativo catastale."""

    sezione_urbana: Annotated[
        str,
        Field(
            max_length=3,
            alias="SEZIONE URBANA",
        ),
    ]
    foglio: Annotated[str, Field(min_length=1, max_length=4, alias="FOGLIO")]
    numero: Annotated[
        str,
        Field(
            max_length=5,
            alias="NUMERO",
        ),
    ]
    denominatore: Annotated[
        str,
        Field(
            max_length=4,
            alias="DENOMINATORE",
        ),
    ]
    subalterno: Annotated[
        str,
        Field(
            max_length=4,
            alias="SUBALTERNO",
        ),
    ]
    edificialita: Annotated[
        str,
        Field(
            max_length=1,
            alias="EDIFICIALITA",
        ),
    ]

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    @field_validator("edificialita")
    @classmethod
    def validate_edificialita(cls, v, info):
        data = info.data
        numero = data.get("numero", "")
        if v == "E" and not numero.startswith("."):
            raise ValueError("Per edificialità 'E', il numero deve iniziare con '.'")
        return v


class Indirizzo(BaseModel):
    """Modello per un singolo indirizzo."""

    toponimo: Annotated[
        str,
        Field(
            min_length=3,
            max_length=3,
            alias="TOPONIMO",
        ),
    ]
    indirizzo: Annotated[
        str,
        Field(
            min_length=1,
            max_length=50,
            alias="INDIRIZZO",
        ),
    ]
    civico1: Annotated[
        str | None,
        Field(
            default=None,
            max_length=6,
            alias="CIVICO 1",
        ),
    ]
    civico2: Annotated[
        str | None,
        Field(
            default=None,
            max_length=6,
            alias="CIVICO 2",
        ),
    ]
    civico3: Annotated[
        str | None,
        Field(
            default=None,
            max_length=6,
            alias="CIVICO 3",
        ),
    ]
    codice_strada: Annotated[
        str,
        Field(
            default=None,
            max_length=5,
            alias="CODICE STRADA",
        ),
    ]

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class UtilitaComune(BaseModel):
    """Modello per una singola utilità comune."""

    sezione_urbana: Annotated[
        str,
        Field(
            default=None,
            max_length=3,
            alias="SEZIONE URBANA",
        ),
    ]
    foglio: Annotated[
        str,
        Field(
            min_length=4,
            max_length=4,
            alias="FOGLIO",
        ),
    ]
    numero: Annotated[
        str,
        Field(
            min_length=5,
            max_length=5,
            alias="NUMERO",
        ),
    ]
    denominatore: Annotated[
        str,
        Field(
            default=None,
            max_length=4,
            alias="DENOMINATORE",
        ),
    ]
    subalterno: Annotated[
        str,
        Field(
            default=None,
            max_length=4,
            alias="SUBALTERNO",
        ),
    ]

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class Riserva(BaseModel):
    """Modello per una singola riserva."""

    codice_riserva: Annotated[
        str, Field(min_length=1, max_length=1, alias="CODICE RISERVA")
    ]
    partita_iscrizione_riserva: Annotated[
        str, Field(default=None, max_length=7, alias="PARTITA ISCRIZIONE RISERVA")
    ]

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class FabbricatiRecord2(BaseRecord):
    """Record di tipo 2: identificativi dell'unità immobiliare."""

    tipo_record: Annotated[
        Literal["2"], Field(min_length=1, max_length=1, alias="TIPO RECORD")
    ]
    identificativi: List[Identificativo]

    @field_validator("identificativi")
    @classmethod
    def check_max_identificativi(cls, v):
        if len(v) > 10:
            raise ValueError("Un record può contenere al massimo 10 identificativi")
        return v


# class FabbricatiRecordUno(FabbricatiRecord):
#     # Dati relativi all'ubicazione dell'immobile
#     # nel fabbricato
#     lotto: str
#     edificio: str
#     scala: str
#     interno1: str
#     interno2: str
#     piano1: str
#     piano2: str
#     piano3: str
#     piano4: str
#     # Dati relativi all'atto che ha generato
#     # la situazione oggettiva dell'unità
#     data_di_efficacia00: str  # TBD to_date
#     data_di_registrazione00: str  # TBD to_date
#     tipo_nota00: str
#     numero_nota00: str
#     progressivo_nota00: str
#     anno_nota00: str
#     data_di_efficacia99: str  # TBD to_date
#     data_di_registrazione99: str  # TBD to_date
#     tipo_nota99: str
#     numero_nota99: str
#     progressivo_nota99: str
#     anno_nota99: str
#     partita: str
#     annotazione: str  # handle accents
#     identificativo_mutazione_iniziale: str
#     identificativo_mutazione_finale: str
#     protocollo_notifica: str
#     data_notifica: str  # TBD to_date
#     # Dati aggiunti dal 2007
#     # Dati relativi all'atto che ha generato
#     # la situazione oggettiva dell'unità
#     codice_causale_atto_generante: str = None
#     descrizione_atto_generante: str = None
#     # Dati relativi all'atto che ha concluso
#     # la situazione oggettiva dell'unità
#     codice_causale_atto_conclusivo: str = None
#     descrizione_atto_conclusivo: str = None
#     flag_classamento: str = None


# class FabbricatiRecordUnoModel(FabbricatiRecordBase, FabbricatiRecordUno):
#     pass


# class FabbricatiRecordDue(FabbricatiRecord, CommonBaseParcel):
#     sezione_urbana: str
#     id_particella: str


# class FabbricatiRecordDueModel(FabbricatiRecordBase, FabbricatiRecordDue):
#     pass


# class FabbricatiRecordDueCross(FabbricatiRecordDueModel):
#     terreno_id: str


class FabbricatiRecord3(BaseRecord):
    """Record di tipo 3: indirizzi dell'unità immobiliare."""

    tipo_record: Annotated[
        Literal["3"], Field(min_length=1, max_length=1, alias="TIPO RECORD")
    ]
    indirizzi: List[Indirizzo]

    @field_validator("indirizzi")
    @classmethod
    def check_max_indirizzi(cls, v):
        if len(v) > 4:
            raise ValueError("Un record può contenere al massimo 4 indirizzi")
        return v


class FabbricatiRecordTre(FabbricatiRecord):
    toponimo: str
    indirizzo: str
    civico1: str
    civico2: str
    civico3: str
    codice_strada: str


class FabbricatiRecordTreModel(FabbricatiRecordBase, FabbricatiRecordTre):
    pass


class FabbricatiRecordQuattro(FabbricatiRecord):
    sezione_urbana: str
    foglio: str
    numero: str
    denominatore: str
    subalterno: str


class FabbricatiRecordQuattroModel(FabbricatiRecordBase, FabbricatiRecordQuattro):
    pass


class FabbricatiRecord4(BaseRecord):
    """Record di tipo 4: utilità comuni dell'unità immobiliare."""

    tipo_record: Annotated[
        Literal["4"], Field(min_length=1, max_length=1, alias="TIPO RECORD")
    ]
    utilita_comuni: List[UtilitaComune]

    @field_validator("utilita_comuni")
    @classmethod
    def check_max_utilita(cls, v):
        if len(v) > 10:
            raise ValueError("Un record può contenere al massimo 10 utilità comuni")
        return v


class FabbricatiRecord5(BaseRecord):
    """Record di tipo 5: riserve dell'unità immobiliare."""

    tipo_record: Annotated[
        Literal["5"], Field(min_length=1, max_length=1, alias="TIPO RECORD")
    ]
    riserve: List[Riserva]

    @field_validator("riserve")
    @classmethod
    def check_max_riserve(cls, v):
        if len(v) > 10:
            raise ValueError("Un record può contenere al massimo 10 riserve")
        return v


# class FabbricatiRecordCinque(FabbricatiRecord):
#     codice_riserva: str
#     partita_iscrizione_riserva: str


# class FabbricatiRecordCinqueModel(FabbricatiRecordBase, FabbricatiRecordCinque):
#     pass


class FabbricatiTerreniModel(BaseModel):
    pass


class FabbricatiImmobile(BaseModel):
    """Modello per rappresentare un immobile completo nel catasto fabbricati."""

    # Campi chiave che identificano l'immobile
    codice_amministrativo: str = Field(...)
    sezione: str = Field(...)
    identificativo_immobile: str = Field(...)
    tipo_immobile: str = Field(...)  # Sempre "F" per i fabbricati
    progressivo: str = Field(...)

    # Record associati all'immobile
    record1: FabbricatiRecord1  # Obbligatorio
    record2: FabbricatiRecord2  # Obbligatorio
    record3: FabbricatiRecord3 | None = None  # Opzionale
    record4: FabbricatiRecord4 | None = None  # Opzionale
    record5: FabbricatiRecord5 | None = None  # Opzionale

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class FabbricatiHeader(BaseModel):
    """Modello per l'intestazione del file dei fabbricati."""

    # Campi dell'intestazione del file
    nome_file: str = Field(...)
    data_creazione: str = Field(...)
    numero_record: int = Field(...)
    codice_comune: str = Field(...)
    sezione: str = " "

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class FabbricatiModel(BaseModel):
    """Modello per rappresentare l'intero contenuto di un file FAB."""

    header: FabbricatiHeader | None = None
    immobili: List[FabbricatiImmobile] = Field(default_factory=list)

    def add_immobile(self, immobile: FabbricatiImmobile) -> None:
        """Aggiunge un immobile alla lista."""
        self.immobili.append(immobile)

    # Eventuali altri metodi utili
    def get_immobile_by_id(
        self, identificativo_immobile: str
    ) -> FabbricatiImmobile | None:
        """Cerca un immobile per identificativo."""
        for immobile in self.immobili:
            if immobile.identificativo_immobile == identificativo_immobile:
                return immobile
        return None


# Modello Pydantic per le informazioni di base di un record
class FabRecordInfo(BaseModel):
    codice_amministrativo: str
    sezione: str
    identificativo_immobile: str
    tipo_immobile: str
    progressivo: str
    tipo_record: str
    data: tuple  # La parte dati dopo il tipo record
    raw_line: str  # Linea completa per riferimento
    raw_tuple: tuple  # Tupla completa degli elementi
    items_number: int  # Numero elementi nel record

    @field_validator("codice_amministrativo")
    @classmethod
    def check_codice_belfiore(cls, v):
        if not (v[1:].isdigit() and len(v[1:]) == 3) or not (
            v[0].isalpha() and len(v[0]) == 1
        ):
            raise ValueError(
                "codice amministrativo deve essere in formato belfiore, es. H501"
            )
        return v

    @field_validator("progressivo")
    @classmethod
    def check_progressivo_numerico(cls, v):
        if not v.isdigit():
            raise ValueError("progressivo deve essere numerico")
        return v

    @field_validator("tipo_record")
    @classmethod
    def check_tipo_record_numerico(cls, v):
        if not v.isdigit():
            raise ValueError("tipo record deve essere numerico")
        return v
