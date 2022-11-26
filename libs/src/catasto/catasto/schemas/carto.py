from typing import Dict
from pydantic import BaseModel, Field, validator


class HeaderModel(BaseModel):
    mappa: str = Field(None, alias="MAPPA")
    nome_mappa: str = Field(None, alias="NOME MAPPA")
    scala_originaria: str = Field(None, alias="SCALA ORIGINARIA")
    oggetti: Dict[str, str] = {}

    @validator("mappa")
    def validate_mappa(cls, val):
        if not val in ["MAPPA", "MAPPA FONDIARIO", "QUADRO D\'UNIONE"]:
            raise ValueError(
                f"The value {val} for MAPPA is not among (MAPPA, MAPPA FONDIARIO, QUADRO D\'UNIONE)"
            )
        return val

    class Config:
        allow_population_by_field_name = True


class LandSheet(BaseModel):
    codice_foglio: str = Field(None, alias="CODICE_FOGLIO")
    codice_comune: str = Field(None, alias="CODICE_COMUNE")
    codice_sezione_censuaria: str = Field(
        None,
        alias="CODICE SEZIONE CENSUARIA"
    )
    codice_numero_foglio: str = Field(
        None,
        alias="CODICE NUMERO FOGLIO"
    )
    numero_foglio: str = Field(
        None,
        alias="NUMERO FOGLIO"
    )
    codice_allegato: str = Field(
        None,
        alias="CODICE ALLEGATO"
    )
    codice_sviluppo: str = Field(
        None,
        alias="CODICE SVILUPPO"
    )
    header: HeaderModel = None

    @validator("codice_sezione_censuaria")
    def validate_codice_sezione_censuaria(cls, val):
        if len(val) != 1:
            raise ValueError(
                "The characters number of CODICE SEZIONE CENSUARIA is not 1"
            )
        if not val in ["A", "B", "C", "D"]:
            raise ValueError(
                f"The value {val} for CODICE SEZIONE CENSUARIA is not among (A, B, C, D)")
        return val

    @validator("codice_allegato")
    def validate_codice_allegato(cls, val):
        if len(val) != 1:
            raise ValueError(
                "The characters number of CODICE ALLEGATO is not 1"
            )
        if not val in ["0", "Q", "A", "B", "D"]:
            raise ValueError(
                f"The value {val} for CODICE ALLEGATO is not among (0, Q, A, B, D)")
        return val

    @validator("codice_sviluppo")
    def validate_codice_sviluppo(cls, val):
        if len(val) != 1:
            raise ValueError(
                "The characters number of CODICE SVILUPPO is not 1"
            )
        if not val in ["A", "B", "C", "D", "0", "U"]:
            raise ValueError(
                f"The value {val} for CODICE SVILUPPO is not among (A, B, C, D, 0, U)"
            )
        return val

    class Config:
        allow_population_by_field_name = True
