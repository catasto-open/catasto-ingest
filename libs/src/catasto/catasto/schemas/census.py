from pydantic import BaseModel, Field, field_validator

from .building import FabbricatiModel, FabbricatiTerreniModel
from .entitlement import TitolaritaModel
from .enumeration import CensusTypeEnum
from .land import TerreniModel
from .subject import SoggettiModel


class CensusFileType(BaseModel):
    filetype: CensusTypeEnum


class CensusFabbricatiFileType(CensusFileType):
    filename: str
    extension: str

    @field_validator("filetype")
    def validate_filetype(cls, val):
        if not val.upper() == CensusTypeEnum.FAB:
            raise ValueError("The type is not FABBRICATI")
        return val.value

    @field_validator("extension")
    def validate_extension(cls, val):
        if not val.upper() == CensusTypeEnum.FAB.name:
            raise ValueError("The extension is not valid for FABBRICATI")
        return val.value


class Census(BaseModel):
    codice_comune: str = Field(..., alias="CODICE_COMUNE")
    sezione: str = Field(None, alias="SEZIONE")
    fabbricati: FabbricatiModel = Field(None, alias="FABBRICATI")
    fabbricati_terreni: FabbricatiTerreniModel = Field(None, alias="FABBRICATI_TERRENI")
    terreni: TerreniModel = Field(None, alias="TERRENI")
    soggetti: SoggettiModel = Field(None, alias="SOGGETTI")
    titolarita: TitolaritaModel = Field(None, alias="TITOLARITA")

    model_config = {
        "populate_by_name": True,
    }
