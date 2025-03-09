from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .common import CommonBase, CommonBaseFiscalSubject, OptionalStr


class TipoSoggettoEnum(Enum):
    PERSONA_FISICA = "P"
    PERSONA_GIURIDICA = "G"


class SessoEnum(Enum):
    MASCHIO = "1"
    FEMMINA = "2"


class SoggettiModel(CommonBase, CommonBaseFiscalSubject):
    pass


class SoggettiRecordBase(BaseModel):
    id_soggetto: str


class SoggettiRecord(SoggettiModel):
    cognome: str = None
    nome: str = None
    sesso: str = None
    data_di_nascita: str = None
    luogo_di_nascita: str = None
    info_suppl: str = None
    denominazione: str = None
    sede: str = None


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
        TipoSoggettoEnum, Field(min_length=1, max_length=1, alias="TIPO SOGGETTO")
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
    def check_tipo_record_numerico(cls, v):
        if v not in ["P", "G"]:
            raise ValueError("tipo soggetto deve essere P o G")
        return v


class SoggettiRecordPrivate(BaseRecord):
    """Record di tipo P: Soggetto persona fisica dell'unità immobiliare."""

    tipo_soggetto: Annotated[
        TipoSoggettoEnum, Field(min_length=1, max_length=1, alias="TIPO SOGGETTO")
    ] = TipoSoggettoEnum.PERSONA_FISICA
    cognome: Annotated[str, Field(min_length=1, max_length=50, alias="COGNOME")]
    nome: Annotated[str, Field(min_length=1, max_length=50, alias="NOME")]
    sesso: Annotated[
        SessoEnum, Field(min_length=1, max_length=1, alias="SESSO")
    ]  # Deve essere "1" per i maschi e "2" per le femmine
    data_di_nascita: Annotated[str, Field(max_length=8, alias="DATA DI NASCITA")]
    luogo_di_nascita: Annotated[
        str, Field(min_length=4, max_length=4, alias="LUOGO DI NASCITA")
    ]
    codice_fiscale: Annotated[
        str, Field(min_length=16, max_length=16, alias="CODICE FISCALE")
    ]
    indicazioni_supplementari: Annotated[
        str, Field(default=None, max_length=16, alias="INDICAZIONI SUPPLEMENTARI")
    ]


class SoggettiRecordGiuridic(BaseRecord):
    """Record di tipo G: Soggetto persona giuridica dell'unità immobiliare."""

    tipo_soggetto: Annotated[
        TipoSoggettoEnum, Field(min_length=1, max_length=1, alias="TIPO SOGGETTO")
    ] = TipoSoggettoEnum.PERSONA_GIURIDICA
    denominazione: Annotated[
        str, Field(min_length=1, max_length=150, alias="DEONOMINAZIONE")
    ]
    sede: Annotated[str, Field(min_length=4, max_length=4, alias="SEDE")]
    codice_fiscale: Annotated[
        str, Field(min_length=11, max_length=11, alias="CODICE FISCALE")
    ]


# Modello Pydantic per le informazioni di base di un record
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
    def check_tipo_record_numerico(cls, v):
        if v not in ["P", "G"]:
            raise ValueError("tipo soggetto deve essere P o G")
        return v
