from typing import Union
from pydantic import BaseModel, AnyUrl, validator
from .enumeration import CensusTypeEnum, CartoTypeEnum


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

    @validator('filetype')
    def validate_filetype(cls, val):
        if val.replace(".", "") not in [
            CensusTypeEnum.FAB.name,
            CensusTypeEnum.SOG.name,
            CensusTypeEnum.TIT.name,
            CensusTypeEnum.TER.name,
            CartoTypeEnum.CXF.name,
            CartoTypeEnum.CTF.name
        ]:
            raise ValueError(
                f"The extension {val} is not valid for Catasto"
            )
        return val


class UrlModel(BaseModel):
    url: AnyUrl
