from typing import Any, Dict

from pydantic import BaseModel, model_validator

from ..building import (
    FabbricatiRecord1,
    FabbricatiRecord2,
    FabbricatiRecord3,
    FabbricatiRecord4,
    FabbricatiRecord5,
    Identificativo,
    Indirizzo,
    UtilitaComune,
)
from ..building import Riserva as FabRiserva
from ..entitlement import Titolarita
from ..land import (
    Deduzione,
    Porzione,
    TerreniRecord1,
    TerreniRecord2,
    TerreniRecord3,
    TerreniRecord4,
)
from ..land import Riserva as TerRiserva
from ..subject import SoggettiModel


def safe_cast(val, to_type, default=None):
    try:
        return to_type(val)
    except (ValueError, TypeError):
        return default


class CatastoBaseModel(BaseModel):
    """Modello base per tutti i modelli Catasto che converte solo stringhe vuote in None."""

    @model_validator(mode="before")
    @classmethod
    def empty_strings_to_none(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Converte solo stringhe vuote in None prima della validazione."""
        if not isinstance(data, dict):
            return data

        for field_name, value in list(data.items()):
            if value == "":  # Solo stringhe vuote, non liste o dizionari vuoti
                data[field_name] = None
        return data


class Cuarcuiu(CatastoBaseModel):
    codice: str
    sezione: str
    immobile: int
    tipo_imm: str
    progressiv: int
    zona: str | None
    categoria: str | None
    classe: str | None
    consistenz: str | None
    superficie: str | None
    rendita_l: str | None
    rendita_e: str | None
    lotto: str | None
    edificio: str | None
    scala: str | None
    interno_1: str | None
    interno_2: str | None
    piano_1: str | None
    piano_2: str | None
    piano_3: str | None
    piano_4: str | None
    gen_eff: str | None
    gen_regist: str | None
    gen_tipo: str | None
    gen_numero: str | None
    gen_progre: str | None
    gen_anno: str | None
    con_eff: str | None
    con_regist: str | None
    con_tipo: str | None
    con_numero: str | None
    con_progre: str | None
    con_anno: str | None
    partita: str | None
    annotazion: str | None
    mutaz_iniz: int | None
    mutaz_fine: int | None
    prot_notif: str | None
    data_notif: str | None
    gen_causa: str | None
    gen_descr: str | None
    con_causa: str | None
    con_descr: str | None
    flag_class: str | None

    def extract_from_model(dati_fabbricato: FabbricatiRecord1):
        return Cuarcuiu(
            codice=dati_fabbricato.codice_amministrativo,
            sezione=dati_fabbricato.sezione,
            immobile=safe_cast(dati_fabbricato.identificativo_immobile, int, None),
            tipo_imm=dati_fabbricato.tipo_immobile,
            progressiv=safe_cast(dati_fabbricato.progressivo, int, None),
            zona=dati_fabbricato.zona,
            categoria=dati_fabbricato.categoria,
            classe=dati_fabbricato.classe,
            consistenz=str(dati_fabbricato.consistenza),
            superficie=str(dati_fabbricato.superficie),
            rendita_l=str(dati_fabbricato.rendita_lire),
            rendita_e=str(dati_fabbricato.rendita_euro),
            lotto=dati_fabbricato.lotto,
            edificio=dati_fabbricato.edificio,
            scala=dati_fabbricato.scala,
            interno_1=dati_fabbricato.interno1,
            interno_2=dati_fabbricato.interno2,
            piano_1=dati_fabbricato.piano1,
            piano_2=dati_fabbricato.piano2,
            piano_3=dati_fabbricato.piano3,
            piano_4=dati_fabbricato.piano4,
            gen_eff=dati_fabbricato.data_efficacia_iniziale,
            gen_regist=dati_fabbricato.data_registrazione_atti_iniziale,
            gen_tipo=dati_fabbricato.tipo_nota_iniziale,
            gen_numero=dati_fabbricato.numero_nota_iniziale,
            gen_progre=dati_fabbricato.progressivo_nota_iniziale,
            gen_anno=dati_fabbricato.anno_nota_iniziale,
            con_eff=dati_fabbricato.data_efficacia_finale,
            con_regist=dati_fabbricato.data_registrazione_atti_finale,
            con_tipo=dati_fabbricato.tipo_nota_finale,
            con_numero=dati_fabbricato.numero_nota_finale,
            con_progre=dati_fabbricato.progressivo_nota_finale,
            con_anno=dati_fabbricato.anno_nota_finale,
            partita=dati_fabbricato.partita,
            annotazion=dati_fabbricato.annotazione,
            mutaz_iniz=safe_cast(
                dati_fabbricato.identificativo_mutazione_iniziale, int, None
            ),
            mutaz_fine=safe_cast(
                dati_fabbricato.identificativo_mutazione_finale, int, None
            ),
            prot_notif=dati_fabbricato.protocollo_notifica,
            data_notif=dati_fabbricato.data_notifica,
            gen_causa=dati_fabbricato.codice_causale_atto_generante,
            gen_descr=dati_fabbricato.descrizione_atto_generante,
            con_causa=dati_fabbricato.codice_causale_atto_conclusivo,
            con_descr=dati_fabbricato.descrizione_atto_conclusivo,
            flag_class=dati_fabbricato.flag_classamento,
        )


class Cuidenti(CatastoBaseModel):
    codice: str
    sezione: str
    immobile: int
    tipo_imm: str
    progressiv: int
    sez_urbana: str | None
    foglio: str | None
    numero: str | None
    denominato: int | None
    subalterno: str | None
    edificiale: str | None

    def extract_from_model(
        dati_fabbricato: FabbricatiRecord2, dati_identificativo: Identificativo
    ):
        return Cuidenti(
            codice=dati_fabbricato.codice_amministrativo,
            sezione=dati_fabbricato.sezione,
            immobile=safe_cast(dati_fabbricato.identificativo_immobile, int, None),
            tipo_imm=dati_fabbricato.tipo_immobile,
            progressiv=safe_cast(dati_fabbricato.progressivo, int, None),
            sez_urbana=dati_identificativo.sezione_urbana,
            foglio=dati_identificativo.foglio,
            numero=dati_identificativo.numero,
            denominato=safe_cast(dati_identificativo.denominatore, int, None),
            subalterno=dati_identificativo.subalterno,
            edificiale=dati_identificativo.edificialita,
        )


class Cuindiri(CatastoBaseModel):
    codice: str
    sezione: str
    immobile: int
    tipo_imm: str
    progressiv: int
    toponimo: int | None
    indirizzo: str | None
    civico1: str | None
    civico2: str | None
    civico3: str | None
    cod_strada: str | None

    def extract_from_model(
        dati_fabbricato: FabbricatiRecord3, dati_indirizzo: Indirizzo
    ):
        return Cuindiri(
            codice=dati_fabbricato.codice_amministrativo,
            sezione=dati_fabbricato.sezione,
            immobile=safe_cast(dati_fabbricato.identificativo_immobile, int, None),
            tipo_imm=dati_fabbricato.tipo_immobile,
            progressiv=safe_cast(dati_fabbricato.progressivo, int, None),
            toponimo=safe_cast(dati_indirizzo.toponimo, int, None),
            indirizzo=dati_indirizzo.indirizzo,
            civico1=dati_indirizzo.civico1,
            civico2=dati_indirizzo.civico2,
            civico3=dati_indirizzo.civico3,
            cod_strada=dati_indirizzo.codice_strada,
        )


class Cuutilit(CatastoBaseModel):
    codice: str
    sezione: str
    immobile: int
    tipo_imm: str
    progressiv: int
    sez_urbana: str | None
    foglio: str | None
    numero: str | None
    denominato: int | None
    subalterno: str | None

    def extract_from_model(
        dati_fabbricato: FabbricatiRecord4, dati_utilita: UtilitaComune
    ):
        return Cuutilit(
            codice=dati_fabbricato.codice_amministrativo,
            sezione=dati_fabbricato.sezione,
            immobile=safe_cast(dati_fabbricato.identificativo_immobile, int, None),
            tipo_imm=dati_fabbricato.tipo_immobile,
            progressiv=safe_cast(dati_fabbricato.progressivo, int, None),
            sez_urbana=dati_utilita.sezione_urbana,
            foglio=dati_utilita.foglio,
            numero=dati_utilita.numero,
            denominato=safe_cast(dati_utilita.denominatore, int, None),
            subalterno=dati_utilita.subalterno,
        )


class Curiserv(CatastoBaseModel):
    codice: str
    sezione: str
    immobile: int
    tipo_imm: str
    progressiv: int
    riserva: str | None
    iscrizione: str | None

    def extract_from_model(
        dati_fabbricato: FabbricatiRecord5, dati_riserva: FabRiserva
    ):
        return Curiserv(
            codice=dati_fabbricato.codice_amministrativo,
            sezione=dati_fabbricato.sezione,
            immobile=safe_cast(dati_fabbricato.identificativo_immobile, int, None),
            tipo_imm=dati_fabbricato.tipo_immobile,
            progressiv=safe_cast(dati_fabbricato.progressivo, int, None),
            riserva=dati_riserva.codice_riserva,
            iscrizione=dati_riserva.partita_iscrizione_riserva,
        )


class Ctpartic(CatastoBaseModel):
    codice: str
    sezione: str
    immobile: int
    tipo_imm: str
    progressiv: int
    foglio: int | None
    numero: str | None
    denominato: int | None
    subalterno: str | None
    edificiale: str | None
    qualita: int | None
    classe: str | None
    ettari: int | None
    are: int | None
    centiare: int | None
    flag_redd: str | None
    flag_porz: str | None
    flag_deduz: str | None
    dominic_l: str | None
    agrario_l: str | None
    dominic_e: str | None
    agrario_e: str | None
    gen_eff: str | None
    gen_regist: str | None
    gen_tipo: str | None
    gen_numero: str | None
    gen_progre: str | None
    gen_anno: int | None
    con_eff: str | None
    con_regist: str | None
    con_tipo: str | None
    con_numero: str | None
    con_progre: str | None
    con_anno: int | None
    partita: str | None
    annotazion: str | None
    mutaz_iniz: int | None
    mutaz_fine: int | None
    gen_causa: str | None
    gen_descr: str | None
    con_causa: str | None
    con_descr: str | None

    def extract_from_model(dati_terreno: TerreniRecord1):
        return Ctpartic(
            codice=dati_terreno.codice_amministrativo,
            sezione=dati_terreno.sezione,
            immobile=safe_cast(dati_terreno.identificativo_immobile, int, None),
            tipo_imm=dati_terreno.tipo_immobile,
            progressiv=safe_cast(dati_terreno.progressivo, int, None),
            foglio=safe_cast(dati_terreno.foglio, int, None),
            numero=dati_terreno.numero,
            denominato=safe_cast(dati_terreno.denominatore, int, None),
            subalterno=dati_terreno.subalterno,
            edificiale=dati_terreno.edificialita,
            qualita=safe_cast(dati_terreno.qualita, int, None),
            classe=dati_terreno.classe,
            ettari=safe_cast(dati_terreno.ettari, int, None),
            are=safe_cast(dati_terreno.are, int, None),
            centiare=safe_cast(dati_terreno.centiare, int, None),
            flag_redd=dati_terreno.flag_reddito,
            flag_porz=dati_terreno.flag_porzione,
            flag_deduz=dati_terreno.flag_deduzioni,
            dominic_l=str(dati_terreno.reddito_dominicale_lire),
            agrario_l=str(dati_terreno.reddito_agrario_lire),
            dominic_e=str(dati_terreno.reddito_dominicale_euro),
            agrario_e=str(dati_terreno.reddito_agrario_euro),
            gen_eff=dati_terreno.data_efficacia_iniziale,
            gen_regist=dati_terreno.data_registrazione_atti_iniziale,
            gen_tipo=dati_terreno.tipo_nota_iniziale,
            gen_numero=dati_terreno.numero_nota_iniziale,
            gen_progre=dati_terreno.progressivo_nota_iniziale,
            gen_anno=safe_cast(dati_terreno.anno_nota_iniziale, int, None),
            con_eff=dati_terreno.data_efficacia_finale,
            con_regist=dati_terreno.data_registrazione_atti_finale,
            con_tipo=dati_terreno.tipo_nota_finale,
            con_numero=dati_terreno.numero_nota_finale,
            con_progre=dati_terreno.progressivo_nota_finale,
            con_anno=safe_cast(dati_terreno.anno_nota_finale, int, None),
            partita=dati_terreno.partita,
            annotazion=dati_terreno.annotazione,
            mutaz_iniz=safe_cast(
                dati_terreno.identificativo_mutazione_iniziale, int, None
            ),
            mutaz_fine=safe_cast(
                dati_terreno.identificativo_mutazione_finale, int, None
            ),
            gen_causa=dati_terreno.codice_causale_atto_generante,
            gen_descr=dati_terreno.descrizione_atto_generante,
            con_causa=dati_terreno.codice_causale_atto_conclusivo,
            con_descr=dati_terreno.descrizione_atto_conclusivo,
        )


class Ctdeduzi(CatastoBaseModel):
    codice: str
    sezione: str
    immobile: int
    tipo_imm: str
    progressiv: int
    deduzione: str | None

    def extract_from_model(dati_terreno: TerreniRecord2, dati_deduzione: Deduzione):
        return Ctdeduzi(
            codice=dati_terreno.codice_amministrativo,
            sezione=dati_terreno.sezione,
            immobile=safe_cast(dati_terreno.identificativo_immobile, int, None),
            tipo_imm=dati_terreno.tipo_immobile,
            progressiv=safe_cast(dati_terreno.progressivo, int, None),
            deduzione=dati_deduzione.simbolo_deduzione,
        )


class Ctriserv(CatastoBaseModel):
    codice: str
    sezione: str
    immobile: int
    tipo_imm: str
    progressiv: int
    riserva: str | None
    iscrizione: str | None

    def extract_from_model(dati_terreno: TerreniRecord3, dati_riserva: TerRiserva):
        return Ctriserv(
            codice=dati_terreno.codice_amministrativo,
            sezione=dati_terreno.sezione,
            immobile=safe_cast(dati_terreno.identificativo_immobile, int, None),
            tipo_imm=dati_terreno.tipo_immobile,
            progressiv=safe_cast(dati_terreno.progressivo, int, None),
            riserva=dati_riserva.codice_riserva,
            iscrizione=dati_riserva.partita_iscrizione_riserva,
        )


class Ctporzio(CatastoBaseModel):
    codice: str
    sezione: str
    immobile: int
    tipo_imm: str
    progressiv: int
    porzione: str | None
    qualita: int | None
    classe: str | None
    ettari: int | None
    are: int | None
    centiare: int | None
    dominic_e: str | None
    agrario_e: str | None

    def extract_from_model(dati_terreno: TerreniRecord4, dati_porzione: Porzione):
        return Ctporzio(
            codice=dati_terreno.codice_amministrativo,
            sezione=dati_terreno.sezione,
            immobile=safe_cast(dati_terreno.identificativo_immobile, int, None),
            tipo_imm=dati_terreno.tipo_immobile,
            progressiv=safe_cast(dati_terreno.progressivo, int, None),
            porzione=dati_porzione.identificativo_porzione,
            qualita=safe_cast(dati_porzione.qualita, int, None),
            classe=dati_porzione.classe,
            ettari=safe_cast(dati_porzione.ettari, int, None),
            are=safe_cast(dati_porzione.are, int, None),
            centiare=safe_cast(dati_porzione.centiare, int, None),
            dominic_e=dati_porzione.reddito_dominicale_euro,
            agrario_e=dati_porzione.reddito_agrario_euro,
        )


class Cttitola(CatastoBaseModel):
    codice: str
    sezione: str
    soggetto: int
    tipo_sog: str
    immobile: int
    tipo_imm: str
    diritto: str
    titolo: str
    numeratore: int
    denominato: int
    regime: str
    rif_regime: int
    gen_valida: str
    gen_nota: str
    gen_numero: str
    gen_progre: str
    gen_anno: str
    gen_regist: str
    partita: str
    con_valida: str
    con_nota: str
    con_numero: str
    con_progre: str
    con_anno: str
    con_regist: str
    mutaz_iniz: int
    mutaz_fine: int
    identifica: int
    gen_causa: str
    gen_descr: str
    con_causa: str
    con_descr: str

    def extract_from_model(dati_titolarita: Titolarita):
        return Cttitola(
            codice=dati_titolarita.codice_amministrativo,
            sezione=dati_titolarita.sezione,
            soggetto=safe_cast(dati_titolarita.identificativo_soggetto, int, None),
            tipo_sog=dati_titolarita.tipo_soggetto,
            immobile=safe_cast(dati_titolarita.identificativo_immobile, int, None),
            tipo_imm=dati_titolarita.tipo_immobile,
            diritto=dati_titolarita.codice_diritto,
            titolo=dati_titolarita.titolo_non_codificato,
            numeratore=safe_cast(dati_titolarita.quota_numeratore, int, None),
            denominato=safe_cast(dati_titolarita.quota_denominatore, int, None),
            regime=safe_cast(dati_titolarita.regime, int, None),
            rif_regime=dati_titolarita.soggetto_di_riferimento,
            gen_valida=dati_titolarita.data_di_validita00,
            gen_nota=dati_titolarita.tipo_nota00,
            gen_numero=dati_titolarita.numero_nota00,
            gen_progre=dati_titolarita.progressivo_nota00,
            gen_anno=dati_titolarita.anno_nota00,
            gen_regist=dati_titolarita.data_registrazione_atti00,
            partita=dati_titolarita.partita,
            con_valida=dati_titolarita.data_di_validita99,
            con_nota=dati_titolarita.tipo_nota99,
            con_numero=dati_titolarita.numero_nota99,
            con_progre=dati_titolarita.progressivo_nota99,
            con_anno=dati_titolarita.anno_nota99,
            con_regist=dati_titolarita.data_registrazione_atti99,
            mutaz_iniz=safe_cast(
                dati_titolarita.identificativo_mutazione_iniziale, int, None
            ),
            mutaz_fine=safe_cast(
                dati_titolarita.identificativo_mutazione_finale, int, None
            ),
            identifica=safe_cast(dati_titolarita.identificativo_titolarita, int, None),
            gen_causa=dati_titolarita.codice_causale_atto_generante,
            gen_descr=dati_titolarita.descrizione_atto_generante,
            con_causa=dati_titolarita.codice_causale_atto_conclusivo,
            con_descr=dati_titolarita.descrizione_atto_conclusivo,
        )


class Ctfisica(CatastoBaseModel):
    codice: str
    sezione: str
    soggetto: int
    tipo_sog: str
    cognome: str
    nome: str
    sesso: str
    data: str
    luogo: str
    codfiscale: str
    supplement: str

    def extract_from_model(dati_soggetto: SoggettiModel):
        return Ctfisica(
            codice=dati_soggetto.codice_amministrativo,
            sezione=dati_soggetto.sezione,
            soggetto=safe_cast(dati_soggetto.identificativo_soggetto, int, None),
            tipo_sog=dati_soggetto.tipo_soggetto,
            cognome=dati_soggetto.cognome,
            nome=dati_soggetto.nome,
            sesso=dati_soggetto.sesso,
            data=dati_soggetto.data_di_nascita,
            luogo=dati_soggetto.luogo_di_nascita,
            codfiscale=dati_soggetto.codice_fiscale,
            supplement=dati_soggetto.info_suppl,
        )


class Ctnonfis(CatastoBaseModel):
    codice: str
    sezione: str
    soggetto: int
    tipo_sog: str
    codfiscale: str
    denominaz: str
    sede: str

    def extract_from_model(dati_soggetto: SoggettiModel):
        return Ctnonfis(
            codice=dati_soggetto.codice_amministrativo,
            sezione=dati_soggetto.sezione,
            soggetto=safe_cast(dati_soggetto.identificativo_soggetto, int, None),
            tipo_sog=dati_soggetto.tipo_soggetto,
            codfiscale=dati_soggetto.codice_fiscale,
            denominaz=dati_soggetto.denominazione,
            sede=dati_soggetto.sede,
        )
