from enum import Enum
from typing import Annotated, List, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .common import OptionalStr


class TipoSoggettoEnum(Enum):
    PERSONA_FISICA = "P"
    PERSONA_GIURIDICA = "G"


class SessoEnum(Enum):
    MASCHIO = "1"
    FEMMINA = "2"


# class SoggettiModel(CommonBase, CommonBaseFiscalSubject):
#     pass


# class SoggettiRecordBase(BaseModel):
#     id_soggetto: str


# class SoggettiRecord(SoggettiModel):
#     cognome: str = None
#     nome: str = None
#     sesso: str = None
#     data_di_nascita: str = None
#     luogo_di_nascita: str = None
#     info_suppl: str = None
#     denominazione: str = None
#     sede: str = None


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

    @field_validator("tipo_soggetto")
    @classmethod
    def check_tipo_soggetto(cls, v):
        if v.value not in ["P", "G"]:
            raise ValueError("tipo soggetto deve essere P o G")
        return v.value


class SoggettiRecordPrivatePerson(BaseRecord):
    """Record di tipo P: Soggetto persona fisica dell'unità immobiliare."""

    tipo_soggetto: Annotated[TipoSoggettoEnum, Field(..., alias="TIPO SOGGETTO")]
    cognome: Annotated[str, Field(min_length=1, max_length=50, alias="COGNOME")]
    nome: Annotated[str, Field(min_length=1, max_length=50, alias="NOME")]
    sesso: Annotated[
        OptionalStr, Field(default=None, alias="SESSO")
    ]  # Deve essere "1" per i maschi e "2" per le femmine
    data_di_nascita: Annotated[str, Field(max_length=8, alias="DATA DI NASCITA")]
    luogo_di_nascita: Annotated[
        OptionalStr, Field(default=None, max_length=4, alias="LUOGO DI NASCITA")
    ]
    codice_fiscale: Annotated[
        OptionalStr, Field(default=None, max_length=16, alias="CODICE FISCALE")
    ]
    indicazioni_supplementari: Annotated[
        str, Field(default=None, max_length=100, alias="INDICAZIONI SUPPLEMENTARI")
    ]

    @field_validator("tipo_soggetto")
    @classmethod
    def check_tipo_privato(cls, v):
        if v != "P":
            raise ValueError("tipo soggetto deve essere P")
        return v

    @field_validator("sesso")
    @classmethod
    def check_sesso(cls, v):
        if v:
            if v not in ["1", "2"]:
                raise ValueError("sesso se esiste deve essere 1 o 2")
        return v


class SoggettiRecordGiuridicPerson(BaseRecord):
    """Record di tipo G: Soggetto persona giuridica dell'unità immobiliare."""

    tipo_soggetto: Annotated[TipoSoggettoEnum, Field(..., alias="TIPO SOGGETTO")]
    denominazione: Annotated[
        str, Field(min_length=1, max_length=150, alias="DEONOMINAZIONE")
    ]
    sede: Annotated[OptionalStr, Field(default=None, max_length=4, alias="SEDE")]
    codice_fiscale: Annotated[
        OptionalStr, Field(default=None, max_length=11, alias="CODICE FISCALE")
    ]

    @field_validator("tipo_soggetto")
    @classmethod
    def check_tipo_giuridico(cls, v):
        if v != "G":
            raise ValueError("tipo soggetto deve essere G")
        return v


class Soggetto(BaseModel):
    """Modello per rappresentare un soggetto completo nel catasto fabbricati."""

    # Campi chiave che identificano il soggetto
    codice_amministrativo: str = Field(...)
    sezione: str = Field(...)
    identificativo_soggetto: str = Field(...)
    tipo_soggetto: str = Field(...)  # "P" o "G"

    # Record associati al soggetto
    record: Union[
        SoggettiRecordPrivatePerson, SoggettiRecordGiuridicPerson
    ]  # Obbligatorio

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class SoggettoHeader(BaseModel):
    """Modello per l'intestazione del file dei soggetti."""

    # Campi dell'intestazione del file
    nome_file: str = Field(...)
    data_creazione: str = Field(...)
    numero_record: int = Field(...)
    codice_comune: str = Field(...)
    sezione: str = " "

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class SoggettiModel(BaseModel):
    """Modello per rappresentare l'intero contenuto di un file FAB."""

    header: SoggettoHeader | None = None
    soggetti: List[Soggetto] = Field(default_factory=list)

    def add_soggetto(self, soggetto: Soggetto) -> None:
        """Aggiunge un soggetto alla lista."""
        self.soggetti.append(soggetto)

    # Eventuali altri metodi utili
    def get_soggetto_by_id(self, identificativo_soggetto: str) -> Soggetto | None:
        """Cerca un soggetto per identificativo."""
        for soggetto in self.soggetti:
            if soggetto.identificativo_soggetto == identificativo_soggetto:
                return soggetto
        return None


# Modello Pydantic per le informazioni dir base di un record
class SogRecordInfo(BaseModel):
    codice_amministrativo: str
    sezione: str
    identificativo_soggetto: str
    tipo_soggetto: str
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

    @field_validator("tipo_soggetto")
    @classmethod
    def check_tipo_soggetto(cls, v):
        if v not in ["P", "G"]:
            raise ValueError("tipo soggetto deve essere P o G")
        return v
