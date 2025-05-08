from typing import Literal

from pydantic import AnyHttpUrl, BaseModel, Field, field_validator

from .enumeration import CartoTypeEnum, CensusTypeEnum

# Tipo per campi opzionali
OptionalStr = str | None


class CommonBase(BaseModel):
    codice_ammvo: str
    sezione: str = None


class CommonBaseBuilding(BaseModel):
    identificativo_immobile: str
    tipo_immobile: str


class CommonBaseRecord(CommonBaseBuilding):
    progressivo: str
    tipo_record: str


class CommonBaseParcel(BaseModel):
    foglio: str
    numero: str
    denominatore: str
    subalterno: str
    edificialita: str


class CommonBaseSubject(BaseModel):
    identificativo_soggetto: str
    tipo_soggetto: str


class CommonBaseFiscalSubject(CommonBaseSubject):
    codice_fiscale: str


class ReaderFile(BaseModel):
    filename: str
    filetype: str
    content: str

    @field_validator("filetype")
    def validate_filetype(cls, val):
        if val.upper().replace(".", "") not in [
            CensusTypeEnum.FAB.name,
            CensusTypeEnum.SOG.name,
            CensusTypeEnum.TIT.name,
            CensusTypeEnum.TER.name,
            CartoTypeEnum.CXF.name,
            CartoTypeEnum.CTF.name,
        ]:
            raise ValueError(f"The extension {val} is not valid for Catasto")
        return val


# Definizioni dei modelli Pydantic (versione semplificata delle classi precedenti)
class BaseRecord(BaseModel):
    """Classe base per tutti i record del file fabbricati."""

    codice_amministrativo: str = Field(..., min_length=4, max_length=4)
    sezione: str = Field(..., min_length=1, max_length=1)
    identificativo_immobile: str = Field(..., max_length=15)
    tipo_immobile: Literal["F"] = Field(...)  # Deve essere 'F' per i fabbricati
    progressivo: str = Field(..., min_length=3, max_length=3)
    tipo_record: str = Field(...)  # Sarà validato dalle sottoclassi

    model_config = {"extra": "forbid"}


class UrlModel(BaseModel):
    url: AnyHttpUrl

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: AnyHttpUrl) -> AnyHttpUrl:
        # I validatori in Pydantic v2 restituiscono il valore validato invece di True/False
        return v
