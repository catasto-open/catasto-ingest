from typing import Dict, List

from pydantic import BaseModel, Field, field_validator


class HeaderModel(BaseModel):
    mappa: str | None = Field(None, alias="MAPPA")
    nome_mappa: str | None = Field(None, alias="NOME MAPPA")
    scala_originaria: str | None = Field(None, alias="SCALA ORIGINARIA")
    oggetti: Dict[str, str] = {}

    @field_validator("mappa")
    def validate_mappa(cls, val):
        if val not in ["MAPPA", "MAPPA FONDIARIO", "QUADRO D'UNIONE"]:
            raise ValueError(
                f"The value {val} for MAPPA is not among (MAPPA, MAPPA FONDIARIO, QUADRO D'UNIONE)"
            )
        return val

    model_config = {"populate_by_name": True}


class CartoObject(BaseModel):
    bordo: List = Field(default_factory=list, alias="BORDO")
    testo: List = Field(default_factory=list, alias="TESTO")
    simbolo: List = Field(default_factory=list, alias="SIMBOLO")
    fiduciale: List = Field(default_factory=list, alias="FIDUCIALE")
    linea: List = Field(default_factory=list, alias="LINEA")
    eof: List = Field(default_factory=list, alias="EOF")


class LandSheet(BaseModel):
    codice_foglio: str | None = Field(None, alias="CODICE_FOGLIO")
    codice_comune: str | None = Field(None, alias="CODICE_COMUNE")
    codice_sezione_censuaria: str | None = Field(None, alias="CODICE SEZIONE CENSUARIA")
    codice_numero_foglio: str | None = Field(None, alias="CODICE NUMERO FOGLIO")
    numero_foglio: str | None = Field(None, alias="NUMERO FOGLIO")
    codice_allegato: str | None = Field(None, alias="CODICE ALLEGATO")
    codice_sviluppo: str | None = Field(None, alias="CODICE SVILUPPO")
    header: HeaderModel | None = None
    oggetti: CartoObject | None = None

    @field_validator("codice_sezione_censuaria")
    def validate_codice_sezione_censuaria(cls, val):
        if len(val) != 1:
            raise ValueError(
                "The characters number of CODICE SEZIONE CENSUARIA is not 1"
            )
        if val not in ["A", "B", "C", "D"]:
            raise ValueError(
                f"The value {val} for CODICE SEZIONE CENSUARIA is not among (A, B, C, D)"
            )
        return val

    @field_validator("codice_allegato")
    def validate_codice_allegato(cls, val):
        if len(val) != 1:
            raise ValueError("The characters number of CODICE ALLEGATO is not 1")
        if val not in ["0", "Q", "A", "B", "D"]:
            raise ValueError(
                f"The value {val} for CODICE ALLEGATO is not among (0, Q, A, B, D)"
            )
        return val

    @field_validator("codice_sviluppo")
    def validate_codice_sviluppo(cls, val):
        if len(val) != 1:
            raise ValueError("The characters number of CODICE SVILUPPO is not 1")
        if val not in ["A", "B", "C", "D", "0", "U"]:
            raise ValueError(
                f"The value {val} for CODICE SVILUPPO is not among (A, B, C, D, 0, U)"
            )
        return val

    model_config = {"populate_by_name": True}


class CartoObjectItem(BaseModel):
    codice_identificativo: str = Field(None, alias="CODICE_IDENTIFICATIVO")
    tipo: str | None = None
    vertici: List = Field(default_factory=list, alias="VERTICI")
    tabisole: List = Field(default_factory=list, alias="TABISOLE")
    numeroisole: str | None = Field(None, alias="NUMEROISOLE")
    numerovertici: str | None = Field(None, alias="NUMEROVERTICI")
