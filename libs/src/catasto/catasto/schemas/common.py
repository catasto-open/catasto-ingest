from pydantic import BaseModel


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