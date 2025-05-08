from enum import Enum


class CartoTypeEnum(Enum):
    CXF = "CARTOGRAFICO"
    CTF = "CARTOGRAFICO ETRF"


class CensusTypeEnum(Enum):
    FAB = "FABBRICATI"
    TER = "TERRENI"
    SOG = "SOGGETTI"
    TIT = "TITOLARITA"
