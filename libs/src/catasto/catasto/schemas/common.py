from pydantic import AnyHttpUrl, BaseModel, field_validator

from .enumeration import CartoTypeEnum, CensusTypeEnum


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
        if val.replace(".", "") not in [
            CensusTypeEnum.FAB.name,
            CensusTypeEnum.SOG.name,
            CensusTypeEnum.TIT.name,
            CensusTypeEnum.TER.name,
            CartoTypeEnum.CXF.name,
            CartoTypeEnum.CTF.name,
        ]:
            raise ValueError(f"The extension {val} is not valid for Catasto")
        return val


class UrlModel(BaseModel):
    url: AnyHttpUrl

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: AnyHttpUrl) -> AnyHttpUrl:
        # I validatori in Pydantic v2 restituiscono il valore validato invece di True/False
        return v
