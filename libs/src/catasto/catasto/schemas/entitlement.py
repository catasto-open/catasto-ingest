from datetime import datetime
from enum import Enum
from typing import Annotated, List

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .common import OptionalStr

# from .common import CommonBase, CommonBaseBuilding, CommonBaseSubject


# class Titolarita(CommonBase, CommonBaseSubject, CommonBaseBuilding):
#     # Dati della titolarità
#     codice_diritto: str
#     titolo_non_codificato: str  # handle accents
#     quota_numeratore: str
#     quota_denominatore: str
#     regime: str
#     soggetto_di_riferimento: str
#     # Dati relativi all'atto che
#     # ha generato la titolarità
#     data_di_validita00: str  # TBD to_date
#     tipo_nota00: str
#     numero_nota00: str
#     progressivo_nota00: str
#     anno_nota00: str
#     data_registrazione_atti00: str  # TBD to_date
#     partita: str
#     # Dati relativi all'atto che ha concluso
#     # la situazione oggettiva dell'unità
#     data_di_validita99: str  # TBD to_date
#     tipo_nota99: str
#     numero_nota99: str
#     progressivo_nota99: str
#     anno_nota99: str
#     data_registrazione_atti99: str  # TBD to_date
#     identificativo_mutazione_iniziale: str
#     identificativo_mutazione_finale: str
#     # Campo introdotto solo dal 2001
#     identificativo_titolarita: str = None
#     # Campi introdotti dal 2007
#     codice_causale_atto_generante: str = None
#     descrizione_atto_generante: str = None
#     codice_causale_atto_conclusivo: str = None
#     descrizione_atto_conclusivo: str = None


# class TitolaritaModel(Titolarita):
#     id_titolarita: str


class TipoSoggettoEnum(Enum):
    PERSONA_FISICA = "P"
    PERSONA_GIURIDICA = "G"


class TipoImmobileEnum(Enum):
    FABBRICATI = "F"
    TERRENI = "T"


class TipoRegimeEnum(Enum):
    VUOTO = " "
    COMUNIONE = "C"
    BENE_PERSONALE = "P"
    IN_SEPARAZIONE = "S"
    IN_COMUNIONE_DE_RESIDUO = "D"


class BaseRecord(BaseModel):
    """Classe base per tutti i record del file soggetti."""

    codice_amministrativo: Annotated[
        str, Field(min_length=4, max_length=4, alias="CODICE AMMINISTRATIVO")
    ]
    sezione: Annotated[OptionalStr, Field(min_length=1, max_length=1, alias="SEZIONE")]
    identificativo_soggetto: Annotated[
        str, Field(max_length=15, alias="IDENTIFICATIVO SOGGETTO")
    ]
    tipo_soggetto: Annotated[
        TipoSoggettoEnum, Field(..., alias="TIPO SOGGETTO")
    ]  # Deve essere "P" per i soggetti privati e "G" per i soggetti giuridici
    identificativo_immobile: Annotated[
        str, Field(max_length=15, alias="IDENTIFICATIVO IMMOBILE")
    ]
    tipo_immobile: Annotated[
        TipoImmobileEnum, Field(..., alias="TIPO IMMOBILE")
    ]  # Deve essere 'F' per i fabbricati e 'T' per i terreni

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

    @field_validator("identificativo_soggetto")
    @classmethod
    def check_identificativo_soggetto_numerico(cls, v):
        if not v.isdigit():
            raise ValueError("identificativo soggetto deve essere numerico")
        return v

    @field_validator("identificativo_immobile")
    @classmethod
    def check_identificativo_immobile_numerico(cls, v):
        if not v.isdigit():
            raise ValueError("identificativo immobile deve essere numerico")
        return v

    @field_validator("tipo_soggetto")
    @classmethod
    def check_tipo_soggetto(cls, v):
        if v.value not in ["P", "G"]:
            raise ValueError("tipo soggetto deve essere P o G")
        return v.value

    @field_validator("tipo_immobile")
    @classmethod
    def check_tipo_immobile(cls, v):
        if v.value not in ["F", "T"]:
            raise ValueError("tipo immobile deve essere F o T")
        return v.value


class Titolarita(BaseRecord):
    """Titolarità dell'unità immobiliare."""

    codice_diritto: Annotated[
        str, Field(min_length=1, max_length=3, alias="CODICE DIRITTO")
    ]
    titolo_non_codificato: Annotated[
        OptionalStr,
        Field(
            default=None, min_length=0, max_length=200, alias="TITOLO NON CODIFICATO"
        ),
    ]
    quota_numeratore: Annotated[str, Field(max_length=15, alias="QUOTA NUMERATORE")]
    quota_denominatore: Annotated[str, Field(max_length=15, alias="QUOTA DENOMINATORE")]
    regime: Annotated[TipoRegimeEnum | None, Field(default=None, alias="REGIME")]
    soggetto_di_riferimento: Annotated[
        str, Field(max_length=15, alias="SOGGETTO DI RIFERIMENTO")
    ]
    data_di_validita_iniziale: Annotated[
        OptionalStr,
        Field(
            default=None,
            max_length=8,
            alias="DATA DI VALIDITA' INIZIALE",
        ),
    ]
    tipo_nota_iniziale: Annotated[
        str, Field(min_length=0, max_length=1, alias="TIPO NOTA INIZIALE")
    ]
    numero_nota_iniziale: Annotated[
        str, Field(min_length=0, max_length=6, alias="NUMERO NOTA INIZIALE")
    ]
    progressivo_nota_iniziale: Annotated[
        str, Field(min_length=0, max_length=3, alias="PROGRESSIVO NOTA INIZIALE")
    ]
    anno_nota_iniziale: Annotated[
        str, Field(min_length=4, max_length=4, alias="ANNO NOTA INIZIALE")
    ]
    data_registrazione_atti_iniziale: Annotated[
        OptionalStr,
        Field(
            default=None,
            max_length=8,
            alias="DATA DI REGISTRAZIONE ATTI INIZIALE",
        ),
    ]
    partita: Annotated[
        OptionalStr,
        Field(
            default=None,
            max_length=7,
            alias="PARTITA",
        ),
    ]
    data_di_validita_finale: Annotated[
        OptionalStr,
        Field(
            default=None,
            max_length=8,
            alias="DATA DI VALIDITA' FINALE",
        ),
    ]
    tipo_nota_finale: Annotated[
        OptionalStr, Field(default=None, max_length=1, alias="TIPO NOTA FINALE")
    ]
    numero_nota_finale: Annotated[
        OptionalStr, Field(default=None, max_length=6, alias="NUMERO NOTA FINALE")
    ]
    progressivo_nota_finale: Annotated[
        OptionalStr, Field(default=None, max_length=3, alias="PROGRESSIVO NOTA FINALE")
    ]
    anno_nota_finale: Annotated[
        OptionalStr, Field(default=None, max_length=4, alias="ANNO NOTA FINALE")
    ]
    data_registrazione_atti_finale: Annotated[
        OptionalStr,
        Field(
            default=None,
            max_length=8,
            alias="DATA DI REGISTRAZIONE ATTI FINALE",
        ),
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
    identificativo_titolarita: Annotated[
        str, Field(max_length=15, alias="IDENTIFICATIVO TITOLARITA'")
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

    model_config = ConfigDict(
        extra="forbid", populate_by_name=True
    )  # Non permettere campi non definiti

    @field_validator("quota_numeratore")
    @classmethod
    def check_quota_numeratore_numerico(cls, v):
        if not v.isdigit():
            raise ValueError("quota numeratore deve essere numerico")
        return v

    @field_validator("quota_denominatore")
    @classmethod
    def check_quota_denominatore_numerico(cls, v):
        if not v.isdigit():
            raise ValueError("quota denominatore deve essere numerico")
        return v

    @field_validator("regime")
    @classmethod
    def check_regime(cls, v):
        if v.value not in [" ", "C", "D", "P", "S"]:
            raise ValueError("tipo soggetto deve essere C, D, P, S o carattere vuoto")
        return v.value

    @field_validator("soggetto_di_riferimento")
    @classmethod
    def check_soggetto_di_riferimento_numerico(cls, v):
        if v and not v.isdigit():
            raise ValueError("soggetto di riferimento deve essere numerico")
        return v

    @field_validator("identificativo_titolarita")
    @classmethod
    def check_identificativo_titolarità_numerico(cls, v):
        if not v.isdigit():
            raise ValueError("identificativo titolarità deve essere numerico")
        return v

    @field_validator(
        "data_di_validita_iniziale",
        "data_di_validita_finale",
        "data_registrazione_atti_iniziale",
        "data_registrazione_atti_finale",
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


class TitolaritaHeader(BaseModel):
    """Modello per l'intestazione del file delle titolarità."""

    # Campi dell'intestazione del file
    nome_file: str = Field(...)
    data_creazione: str = Field(...)
    numero_record: int = Field(...)
    codice_comune: str = Field(...)

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class TitolaritaModel(BaseModel):
    """Modello per rappresentare l'intero contenuto di un file TIT."""

    header: TitolaritaHeader | None = None
    titolarita: List[Titolarita] = Field(default_factory=list)

    def add_titolarita(self, titolarita: Titolarita) -> None:
        """Aggiunge una titolarità alla lista."""
        self.titolarita.append(titolarita)

    # Eventuali altri metodi utili
    def get_titolarita_by_immobile(
        self, identificativo_immobile: str
    ) -> List[Titolarita]:
        """Cerca tutte le titolarità per un immobile."""
        return [
            titolarita
            for titolarita in self.titolarita
            if titolarita.identificativo_immobile == identificativo_immobile
        ]

    def get_titolarita_by_soggetto(
        self, identificativo_soggetto: str
    ) -> List[Titolarita]:
        """Cerca tutte le titolarità per un soggetto."""
        return [
            titolarita
            for titolarita in self.titolarita
            if titolarita.identificativo_soggetto == identificativo_soggetto
        ]


class TitRecordInfo(BaseModel):
    """Modello Pydantic per le informazioni di base di un record di titolarità."""

    codice_amministrativo: str
    sezione: str
    identificativo_soggetto: str
    tipo_soggetto: str
    identificativo_immobile: str
    tipo_immobile: str
    data: tuple  # La parte dati dopo i campi base
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

    @field_validator("identificativo_soggetto")
    @classmethod
    def check_identificativo_soggetto_numerico(cls, v):
        if not v.isdigit():
            raise ValueError("identificativo soggetto deve essere numerico")
        return v

    @field_validator("identificativo_immobile")
    @classmethod
    def check_identificativo_immobile_numerico(cls, v):
        if not v.isdigit():
            raise ValueError("identificativo immobile deve essere numerico")
        return v

    @field_validator("tipo_soggetto")
    @classmethod
    def check_tipo_soggetto(cls, v):
        if v not in ["P", "G"]:
            raise ValueError("tipo soggetto deve essere P o G")
        return v

    @field_validator("tipo_immobile")
    @classmethod
    def check_tipo_immobile(cls, v):
        if v not in ["F", "T"]:
            raise ValueError("tipo immobile deve essere F o T")
        return v
