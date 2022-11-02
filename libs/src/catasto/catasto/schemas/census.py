from pydantic import BaseModel, Field, validator
from .enumeration import CensusTypeEnum
from .building import FabbricatiModel, FabbricatiTerreniModel
from .land import TerreniModel
from .subject import SoggettiModel
from .entitlement import TitolaritaModel


class CensusFileType(BaseModel):
    filetype: CensusTypeEnum


class CensusFabbricatiFileType(CensusFileType):
    filename: str
    extension: str

    @validator('filetype')
    def validate_filetype(cls, val):
        if not val == CensusTypeEnum.FAB:
            raise ValueError('The type is not FABBRICATI')
        return val.value

    @validator('extension')
    def validate_extension(cls, val):
        if not val == CensusTypeEnum.FAB.name:
            raise ValueError('The extension is not valid for FABBRICATI')
        return val.value


class Census(BaseModel):
    codice_comune: str = Field(..., alias="CODICE_COMUNE")
    sezione: str = Field(None, alias="SEZIONE")
    fabbricati: FabbricatiModel = Field(None, alias="FABBRICATI")
    fabbricati_terreni: FabbricatiTerreniModel = Field(None, alias="FABBRICATI_TERRENI")
    terreni: TerreniModel = Field(None, alias="TERRENI")
    soggetti: SoggettiModel = Field(None, alias="SOGGETTI")
    titolarita: TitolaritaModel = Field(None, alias="TITOLARITA")
