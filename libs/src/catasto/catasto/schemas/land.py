from datetime import datetime
from typing import Annotated, List, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .common import CommonBase, CommonBaseRecord, OptionalStr


class TerreniModel(CommonBase, CommonBaseRecord):
    pass


class TerreniRecordBase(BaseModel):
    id_immobile: str


class TerreniRecord(TerreniModel):
    zona: str
    categoria: str
    classe: str
    consistenza: float
    superficie: float
    rendita_lire: float
    rendita_euro: float


class BaseRecord(BaseModel):
    """Classe base per tutti i record del file terreni."""

    codice_amministrativo: Annotated[
        str, Field(min_length=4, max_length=4, alias="CODICE AMMINISTRATIVO")
    ]
    sezione: Annotated[OptionalStr, Field(min_length=1, max_length=1, alias="SEZIONE")]
    identificativo_immobile: Annotated[
        str, Field(max_length=15, alias="IDENTIFICATIVO IMMOBILE")
    ]
    tipo_immobile: Annotated[
        Literal["T"], Field(min_length=1, max_length=1, alias="TIPO IMMOBILE")
    ]  # Deve essere 'T' per i terreni
    progressivo: Annotated[str, Field(min_length=1, max_length=3, alias="PROGRESSIVO")]
    tipo_record: Annotated[
        str, Field(min_length=1, max_length=1, alias="TIPO RECORD")
    ]  # Sarà validato dalle sottoclassi

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

    @field_validator("progressivo")
    @classmethod
    def check_progressivo_numerico(cls, v):
        if not v.isdigit():
            raise ValueError("progressivo deve essere numerico")
        return v

    @field_validator("tipo_record")
    @classmethod
    def check_tipo_record_numerico(cls, v):
        if not v.isdigit():
            raise ValueError("tipo record deve essere numerico")
        return v


class TerreniRecord1(BaseRecord):
    """Record di tipo 1: caratteristiche dell'unità immobiliare."""

    tipo_record: Annotated[
        Literal["1"], Field(min_length=1, max_length=1, alias="TIPO RECORD")
    ]

    # Elementi identificativi della particella
    foglio: Annotated[str, Field(min_length=1, max_length=4, alias="FOGLIO")]
    numero: Annotated[
        str,
        Field(
            max_length=5,
            alias="NUMERO",
        ),
    ]
    denominatore: Annotated[
        str,
        Field(
            max_length=4,
            alias="DENOMINATORE",
        ),
    ]
    subalterno: Annotated[
        str,
        Field(
            max_length=4,
            alias="SUBALTERNO",
        ),
    ]
    edificialita: Annotated[
        str,
        Field(
            max_length=1,
            alias="EDIFICIALITA",
        ),
    ]

    # Dati caratteristici della particella
    qualita: Annotated[
        str,
        Field(
            max_length=3,
            alias="QUALITA",
        ),
    ]
    classe: Annotated[
        str,
        Field(
            max_length=2,
            alias="CLASSE",
        ),
    ]
    ettari: Annotated[
        str,
        Field(
            max_length=5,
            alias="ETTARI",
        ),
    ]
    are: Annotated[
        str,
        Field(
            max_length=2,
            alias="ARE",
        ),
    ]
    centiare: Annotated[
        str,
        Field(
            max_length=2,
            alias="CENTIARE",
        ),
    ]

    # Dati relativi al reddito
    flag_reddito: Annotated[
        OptionalStr,
        Field(
            default=None,
            max_length=1,
            alias="FLAG REDDITO",
        ),
    ]
    flag_porzione: Annotated[
        OptionalStr,
        Field(
            default=None,
            max_length=1,
            alias="FLAG PORZIONE",
        ),
    ]
    flag_deduzioni: Annotated[
        str | None,
        Field(
            default=None,
            max_length=1,
            alias="FLAG DEDUZIONI",
        ),
    ]
    reddito_dominicale_lire: Annotated[
        OptionalStr,
        Field(default=None, max_length=9, alias="REDDITO-DOMINICALE LIRE"),
    ]
    reddito_agrario_lire: Annotated[
        OptionalStr,
        Field(default=None, max_length=8, alias="REDDITO-AGRARIO LIRE"),
    ]
    reddito_dominicale_euro: Annotated[
        OptionalStr,
        Field(default=None, max_length=12, alias="REDDITO-DOMINICALE EURO"),
    ]
    reddito_agrario_euro: Annotated[
        OptionalStr,
        Field(default=None, max_length=11, alias="REDDITO-AGRARIO EURO"),
    ]

    # Dati relativi all'atto che ha generato la situazione oggettiva
    data_efficacia_iniziale: Annotated[
        str, Field(max_length=8, alias="DATA DI EFFICACIA INIZIALE")
    ]
    data_registrazione_atti_iniziale: Annotated[
        str,
        Field(
            min_length=0, max_length=8, alias="DATA DI REGISTRAZIONE IN ATTI INIZIALE"
        ),
    ]
    tipo_nota_iniziale: Annotated[
        str, Field(min_length=0, max_length=1, alias="TIPO NOTA INIZIALE")
    ]
    numero_nota_iniziale: Annotated[
        str, Field(min_length=0, max_length=6, alias="NUMERO NOTA INIZIALE")
    ]
    progressivo_nota_iniziale: Annotated[
        str, Field(min_length=0, max_length=3, alias="PROGRESSIVO NOTA INIZIALE")
    ]
    anno_nota_iniziale: Annotated[
        str, Field(min_length=4, max_length=4, alias="ANNO NOTA INIZIALE")
    ]

    # Dati relativi all'atto che ha concluso la situazione oggettiva
    data_efficacia_finale: Annotated[
        OptionalStr,
        Field(default=None, max_length=8, alias="DATA DI EFFICACIA FINALE"),
    ]
    data_registrazione_atti_finale: Annotated[
        OptionalStr,
        Field(
            default=None,
            max_length=8,
            alias="DATA DI REGISTRAZIONE IN ATTI FINALE",
        ),
    ]
    tipo_nota_finale: Annotated[
        OptionalStr, Field(default=None, max_length=1, alias="TIPO NOTA FINALE")
    ]
    numero_nota_finale: Annotated[
        OptionalStr,
        Field(default=None, max_length=6, alias="NUMERO NOTA FINALE"),
    ]
    progressivo_nota_finale: Annotated[
        OptionalStr,
        Field(default=None, max_length=3, alias="PROGRESSIVO NOTA FINALE"),
    ]
    anno_nota_finale: Annotated[
        OptionalStr, Field(default=None, max_length=4, alias="ANNO NOTA FINALE")
    ]

    # Altri campi
    partita: Annotated[OptionalStr, Field(default=None, max_length=7, alias="PARTITA")]
    annotazione: Annotated[
        OptionalStr, Field(default=None, max_length=200, alias="ANNOTAZIONE")
    ]
    identificativo_mutazione_iniziale: Annotated[
        OptionalStr,
        Field(
            default=None,
            max_length=9,
            alias="IDENTIFICATIVO MUTAZIONE INIZIALE",
        ),
    ]
    identificativo_mutazione_finale: Annotated[
        str | None,
        Field(
            default=None,
            max_length=9,
            alias="IDENTIFICATIVO MUTAZIONE FINALE",
        ),
    ]
    codice_causale_atto_generante: Annotated[
        OptionalStr,
        Field(
            default=None,
            max_length=3,
            alias="CODICE CAUSALE ATTO GENERANTE",
        ),
    ]
    descrizione_atto_generante: Annotated[
        OptionalStr,
        Field(
            default=None,
            max_length=100,
            alias="DESCRIZIONE ATTO GENERANTE",
        ),
    ]
    codice_causale_atto_conclusivo: Annotated[
        OptionalStr,
        Field(
            default=None,
            max_length=3,
            alias="CODICE CAUSALE ATTO CONCLUSIVO",
        ),
    ]
    descrizione_atto_conclusivo: Annotated[
        OptionalStr,
        Field(
            default=None,
            max_length=100,
            alias="DESCRIZIONE ATTO CONCLUSIVO",
        ),
    ]

    @field_validator("foglio")
    @classmethod
    def check_foglio_numerico(cls, v):
        if v and not v.isdigit():
            raise ValueError("foglio deve essere numerico")
        return v

    @field_validator("denominatore")
    @classmethod
    def check_denominatore_numerico(cls, v):
        if v and not v.isdigit():
            raise ValueError("denominatore deve essere numerico")
        return v

    @field_validator("edificialita")
    @classmethod
    def validate_edificialita(cls, v, info):
        data = info.data
        numero = data.get("numero", "")
        if v == "E" and not numero.startswith("."):
            raise ValueError("Per edificialità 'E', il numero deve iniziare con '.'")
        return v

    @field_validator("qualita")
    @classmethod
    def check_qualita_numerico(cls, v):
        if v and not v.isdigit():
            raise ValueError("qualità deve essere numerico")
        return v

    @field_validator("ettari")
    @classmethod
    def check_ettari_numerico(cls, v):
        if v and not v.isdigit():
            raise ValueError("ettari deve essere numerico")
        return v

    @field_validator("are")
    @classmethod
    def check_are_numerico(cls, v):
        if v and not v.isdigit():
            raise ValueError("are deve essere numerico")
        return v

    @field_validator("centiare")
    @classmethod
    def check_centiare_numerico(cls, v):
        if v and not v.isdigit():
            raise ValueError("centiare deve essere numerico")
        return v

    @field_validator("flag_reddito", "flag_porzione", "flag_deduzioni")
    @classmethod
    def validate_flag(cls, v):
        if not v:
            return v
        valid_flags = ["0", "1", " "]
        if v not in valid_flags:
            raise ValueError(f"Flag non valido. Deve essere uno tra {valid_flags}")
        return v

    @field_validator("reddito_dominicale_euro", "reddito_agrario_euro")
    @classmethod
    def validate_reddito_euro(cls, v):
        # Gli ultimi 1/2 caratteri sono decimali
        # se ci sono
        if "," in v:
            decimal = v.split(",")[1]
            if len(decimal) < 1:
                raise ValueError(
                    "Reddito Euro non valido. Gli ultimi 2 caratteri devono essere decimali"
                )
        return v

    @field_validator(
        "data_efficacia_iniziale",
        "data_registrazione_atti_iniziale",
        "data_efficacia_finale",
        "data_registrazione_atti_finale",
    )
    @classmethod
    def validate_date(cls, v):
        """Valida che il campo contenga una data nel formato GGMMAAAA."""
        if not v:
            return v

        # Verifica la lunghezza esatta
        if len(v) != 8:
            raise ValueError(f"La data deve avere esattamente 8 caratteri: {v}")

        # Verifica che siano tutti numeri
        if not v.isdigit():
            raise ValueError(f"La data deve contenere solo cifre numeriche: {v}")

        # Estrai giorno, mese e anno
        giorno, mese, anno = v[:2], v[2:4], v[4:]

        try:
            # Verifica che siano validi come numeri
            g, m, a = int(giorno), int(mese), int(anno)

            # Verifica intervalli validi
            if not (1 <= g <= 31):
                raise ValueError(f"Giorno non valido: {giorno}")
            if not (1 <= m <= 12):
                raise ValueError(f"Mese non valido: {mese}")
            if not (1900 <= a <= 2999):  # Intervallo ragionevole di anni
                raise ValueError(f"Anno non valido: {anno}")

            # Prova a creare un oggetto datetime per verificare la validità completa
            datetime(a, m, g)

            return v
        except ValueError as e:
            raise ValueError(f"Data non valida ({v}): {str(e)}")

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class Deduzione(BaseModel):
    """Modello per una singola deduzione catastale."""

    simbolo_deduzione: Annotated[
        str,
        Field(
            max_length=6,
            alias="SIMBOLO DEDUZIONE",
        ),
    ]

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class Riserva(BaseModel):
    """Modello per una singola riserva."""

    codice_riserva: Annotated[
        str, Field(min_length=1, max_length=1, alias="CODICE RISERVA")
    ]
    partita_iscrizione_riserva: Annotated[
        str, Field(default=None, max_length=7, alias="PARTITA ISCRIZIONE RISERVA")
    ]

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class Porzione(BaseModel):
    """Modello per una singola porzione."""

    identificativo_porzione: Annotated[
        str, Field(min_length=1, max_length=2, alias="IDENTIFICATIVO PORZIONE")
    ]
    qualita: Annotated[
        str,
        Field(
            max_length=3,
            alias="QUALITA",
        ),
    ]
    classe: Annotated[
        str,
        Field(
            max_length=2,
            alias="CLASSE",
        ),
    ]
    ettari: Annotated[
        str,
        Field(
            max_length=5,
            alias="ETTARI",
        ),
    ]
    are: Annotated[
        str,
        Field(
            max_length=2,
            alias="ARE",
        ),
    ]
    centiare: Annotated[
        str,
        Field(
            max_length=2,
            alias="CENTIARE",
        ),
    ]

    @field_validator("qualita")
    @classmethod
    def check_qualita_numerico(cls, v):
        if v and not v.isdigit():
            raise ValueError("qualità deve essere numerico")
        return v

    @field_validator("ettari")
    @classmethod
    def check_ettari_numerico(cls, v):
        if not v.isdigit():
            raise ValueError("ettari deve essere numerico")
        return v

    @field_validator("are")
    @classmethod
    def check_are_numerico(cls, v):
        if not v.isdigit():
            raise ValueError("are deve essere numerico")
        return v

    @field_validator("centiare")
    @classmethod
    def check_centiare_numerico(cls, v):
        if not v.isdigit():
            raise ValueError("centiare deve essere numerico")
        return v

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class PorzioneSdi(Porzione):
    """Modello per una singola porzione dal sistema di interscambio."""

    reddito_dominicale_euro: Annotated[
        OptionalStr,
        Field(default=None, max_length=11, alias="REDDITO-DOMINICALE EURO"),
    ]
    reddito_agrario_euro: Annotated[
        OptionalStr,
        Field(default=None, max_length=11, alias="REDDITO-AGRARIO EURO"),
    ]

    @field_validator("reddito_dominicale_euro", "reddito_agrario_euro")
    @classmethod
    def validate_reddito_euro(cls, v):
        # Gli ultimi 1/2 caratteri sono decimali
        # se ci sono
        if "," in v:
            decimal = v.split(",")[1]
            if len(decimal) < 1:
                raise ValueError(
                    "Reddito Euro non valido. Gli ultimi 2 caratteri devono essere decimali"
                )
        return v

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class TerreniRecord2(BaseRecord):
    """Record di tipo 2: deduzioni dell'unità immobiliare."""

    tipo_record: Annotated[
        Literal["2"], Field(min_length=1, max_length=1, alias="TIPO RECORD")
    ]
    deduzioni: List[Deduzione]

    @field_validator("deduzioni")
    @classmethod
    def check_max_deduzioni(cls, v):
        if len(v) > 7:
            raise ValueError("Un record può contenere al massimo 7 deduzioni")
        return v


class TerreniRecord3(BaseRecord):
    """Record di tipo 3: riserve dell'unità immobiliare."""

    tipo_record: Annotated[
        Literal["3"], Field(min_length=1, max_length=1, alias="TIPO RECORD")
    ]
    riserve: List[Riserva]

    @field_validator("riserve")
    @classmethod
    def check_max_riserve(cls, v):
        if len(v) > 10:
            raise ValueError("Un record può contenere al massimo 10 riserve")
        return v


class TerreniRecord4(BaseRecord):
    """Record di tipo 4: porzioni dell'unità immobiliare."""

    tipo_record: Annotated[
        Literal["4"], Field(min_length=1, max_length=1, alias="TIPO RECORD")
    ]

    porzioni: Union[List[Porzione], List[PorzioneSdi]]

    @field_validator("porzioni")
    @classmethod
    def check_max_porzioni(cls, v):
        if len(v) > 20:
            raise ValueError("Un record può contenere al massimo 20 porzioni")
        return v


class TerreniImmobile(BaseModel):
    """Modello per rappresentare un immobile completo nel catasto terreni."""

    # Campi chiave che identificano l'immobile
    codice_amministrativo: str = Field(...)
    sezione: str = Field(...)
    identificativo_immobile: str = Field(...)
    tipo_immobile: str = Field(...)  # Sempre "T" per i terreni
    progressivo: str = Field(...)

    # Record associati all'immobile
    record1: TerreniRecord1  # Obbligatorio
    record2: TerreniRecord2 | None = None  # Opzionale
    record3: TerreniRecord3 | None = None  # Opzionale
    record4: TerreniRecord4 | None = None  # Opzionale

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class TerreniHeader(BaseModel):
    """Modello per l'intestazione del file dei terreni."""

    # Campi dell'intestazione del file
    nome_file: str = Field(...)
    data_creazione: str = Field(...)
    numero_record: int = Field(...)
    codice_comune: str = Field(...)
    sezione: str = " "

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class TerreniModel(BaseModel):
    """Modello per rappresentare l'intero contenuto di un file TER."""

    header: TerreniHeader | None = None
    immobili: List[TerreniImmobile] = Field(default_factory=list)

    def add_immobile(self, immobile: TerreniImmobile) -> None:
        """Aggiunge un immobile alla lista."""
        self.immobili.append(immobile)

    # Eventuali altri metodi utili
    def get_immobile_by_id(
        self, identificativo_immobile: str
    ) -> TerreniImmobile | None:
        """Cerca un immobile per identificativo."""
        for immobile in self.immobili:
            if immobile.identificativo_immobile == identificativo_immobile:
                return immobile
        return None


# Modello Pydantic per le informazioni di base di un record
class TerRecordInfo(BaseModel):
    codice_amministrativo: str
    sezione: str
    identificativo_immobile: str
    tipo_immobile: str
    progressivo: str
    tipo_record: str
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

    @field_validator("identificativo_immobile")
    @classmethod
    def check_identificativo_immobile_numerico(cls, v):
        if not v.isdigit():
            raise ValueError("identificativo immobile deve essere numerico")
        return v

    @field_validator("progressivo")
    @classmethod
    def check_progressivo_numerico(cls, v):
        if not v.isdigit():
            raise ValueError("progressivo deve essere numerico")
        return v

    @field_validator("tipo_record")
    @classmethod
    def check_tipo_record_numerico(cls, v):
        if not v.isdigit():
            raise ValueError("tipo record deve essere numerico")
        return v
