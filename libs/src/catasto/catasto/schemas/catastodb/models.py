from pydantic import BaseModel
from ..building import (
    FabbricatiRecordUno, FabbricatiRecordTre, FabbricatiRecordQuattro, FabbricatiRecordCinque
)
from ..entitlement import (
    Titolarita
)
from ..subject import (
    SoggettiModel
)
from ..land import (
    TerreniRecordUno, TerreniRecordDue, TerreniRecordTre, TerreniRecordQuattroModel
)

def safe_cast(val, to_type, default=None):
    try:
        return to_type(val)
    except (ValueError, TypeError):
        return default

class Cuarcuiu(BaseModel):
    codice: str
    sezione: str
    immobile: int
    tipo_imm: str
    progressiv: int
    zona: str
    categoria: str
    classe: str
    consistenz: str
    superficie: str
    rendita_l: str
    rendita_e: str
    lotto: str
    edificio: str
    scala: str
    interno_1: str
    interno_2: str
    piano_1: str
    piano_2: str
    piano_3: str
    piano_4: str
    gen_eff: str
    gen_regist: str
    gen_tipo: str
    gen_numero: str
    gen_progre: str
    gen_anno: str
    con_eff: str
    con_regist: str
    con_tipo: str
    con_numero: str
    con_progre: str
    con_anno: str
    partita: str
    annotazion: str
    mutaz_iniz: int
    mutaz_fine: int
    prot_notif: str
    data_notif: str
    gen_causa: str
    gen_descr: str
    con_causa: str
    con_descr: str
    flag_class: str

    def extract_from_model(dati_fabbricato: FabbricatiRecordUno):
        return Cuarcuiu(codice = dati_fabbricato.codice_ammvo,
                        sezione = dati_fabbricato.sezione,
                        immobile = safe_cast(dati_fabbricato.identificativo_immobile, int, None),
                        tipo_imm = dati_fabbricato.tipo_immobile,
                        progressiv = safe_cast(dati_fabbricato.progressivo, int, None),
                        zona = dati_fabbricato.zona,
                        categoria = dati_fabbricato.categoria,
                        classe = dati_fabbricato.classe,
                        consistenz = str(dati_fabbricato.consistenza),
                        superficie = str(dati_fabbricato.superficie),
                        rendita_l = str(dati_fabbricato.rendita_lire),
                        rendita_e = str(dati_fabbricato.rendita_euro),
                        lotto = dati_fabbricato.lotto,
                        edificio = dati_fabbricato.edificio,
                        scala = dati_fabbricato.scala,
                        interno_1 = dati_fabbricato.interno1,
                        interno_2 = dati_fabbricato.interno2,
                        piano_1 = dati_fabbricato.piano1,
                        piano_2 = dati_fabbricato.piano2,
                        piano_3 = dati_fabbricato.piano3,
                        piano_4 = dati_fabbricato.piano4,
                        gen_eff = dati_fabbricato.data_di_efficacia00,
                        gen_regist = dati_fabbricato.data_di_registrazione00,
                        gen_tipo = dati_fabbricato.tipo_nota00,
                        gen_numero = dati_fabbricato.numero_nota00,
                        gen_progre = dati_fabbricato.progressivo_nota00,
                        gen_anno = dati_fabbricato.anno_nota00,
                        con_eff = dati_fabbricato.data_di_efficacia99,
                        con_regist = dati_fabbricato.data_di_registrazione99,
                        con_tipo = dati_fabbricato.tipo_nota99,
                        con_numero = dati_fabbricato.numero_nota99,
                        con_progre = dati_fabbricato.progressivo_nota99,
                        con_anno = dati_fabbricato.anno_nota99,
                        partita = dati_fabbricato.partita,
                        annotazion = dati_fabbricato.annotazione,
                        mutaz_iniz = safe_cast(dati_fabbricato.identificativo_mutazione_iniziale, int, None),
                        mutaz_fine = safe_cast(dati_fabbricato.identificativo_mutazione_finale, int, None),
                        prot_notif = dati_fabbricato.protocollo_notifica,
                        data_notif = dati_fabbricato.data_notifica,
                        gen_causa = dati_fabbricato.codice_causale_atto_generante,
                        gen_descr = dati_fabbricato.descrizione_atto_generante,
                        con_causa = dati_fabbricato.codice_causale_atto_conclusivo,
                        con_descr = dati_fabbricato.descrizione_atto_conclusivo,
                        flag_class = dati_fabbricato.flag_classamento)

class Cuindiri(BaseModel):
    codice: str
    sezione: str
    immobile: int
    tipo_imm: str
    progressiv: int
    toponimo: int
    indirizzo: str
    civico1: str
    civico2: str
    civico3: str
    cod_strada: str

    def extract_from_model(dati_fabbricato: FabbricatiRecordTre):
        return Cuindiri(codice = dati_fabbricato.codice_ammvo,
                        sezione = dati_fabbricato.sezione,
                        immobile = safe_cast(dati_fabbricato.identificativo_immobile, int, None),
                        tipo_imm = dati_fabbricato.tipo_immobile,
                        progressiv = safe_cast(dati_fabbricato.progressivo, int, None),
                        toponimo = safe_cast(dati_fabbricato.toponimo, int, None),
                        indirizzo = dati_fabbricato.indirizzo,
                        civico1 = dati_fabbricato.civico1,
                        civico2 = dati_fabbricato.civico2,
                        civico3 = dati_fabbricato.civico3,
                        cod_strada = dati_fabbricato.codice_strada)


class Cuidenti(BaseModel):
    codice: str
    sezione: str
    immobile: int
    tipo_imm: str
    progressiv: int
    sez_urbana: str
    foglio: str
    numero: str
    denominato: int
    subalterno: str
    edificiale: str

    def extract_from_model(dati_fabbricato: FabbricatiRecordQuattro):
        return Cuidenti(codice = dati_fabbricato.codice_ammvo,
                        sezione = dati_fabbricato.sezione,
                        immobile = safe_cast(dati_fabbricato.identificativo_immobile, int, None),
                        tipo_imm = dati_fabbricato.tipo_immobile,
                        progressiv = safe_cast(dati_fabbricato.progressivo, int, None),
                        sez_urbana = dati_fabbricato.sezione_urbana,
                        foglio = dati_fabbricato.foglio,
                        numero = dati_fabbricato.numero,
                        denominato = safe_cast(dati_fabbricato.denominatore, int, None),
                        subalterno = dati_fabbricato.subalterno,
                        edificiale = None)

class Curiserv(BaseModel):
    codice: str
    sezione: str
    immobile: int
    tipo_imm: str
    progressiv: int
    riserva: str
    iscrizione: str

    def extract_from_model(dati_fabbricato: FabbricatiRecordCinque):
        return Curiserv(codice = dati_fabbricato.codice_ammvo,
                        sezione = dati_fabbricato.sezione,
                        immobile = safe_cast(dati_fabbricato.identificativo_immobile, int, None),
                        tipo_imm = dati_fabbricato.tipo_immobile,
                        progressiv = safe_cast(dati_fabbricato.progressivo, int, None),
                        riserva = dati_fabbricato.codice_riserva,
                        iscrizione = dati_fabbricato.partita_iscrizione_riserva)

class Ctpartic(BaseModel):
    codice: str
    sezione: str
    immobile: int
    tipo_imm: str
    progressiv: int
    foglio: int
    numero: str
    denominato: int
    subalterno: str
    edificiale: str
    qualita: int
    classe: str
    ettari: int
    are: int
    centiare: int
    flag_redd: str
    flag_porz: str
    flag_deduz: str
    dominic_l: str
    agrario_l: str
    dominic_e: str
    agrario_e: str
    gen_eff: str
    gen_regist: str
    gen_tipo: str
    gen_numero: str
    gen_progre: str
    gen_anno: int
    con_eff: str
    con_regist: str
    con_tipo: str
    con_numero: str
    con_progre: str
    con_anno: int
    partita: str
    annotazion: str
    mutaz_iniz: int
    mutaz_fine: int
    gen_causa: str
    gen_descr: str
    con_causa: str
    con_descr: str

    def extract_from_model(dati_terreno: TerreniRecordUno):
        return Ctpartic(codice = dati_terreno.codice_ammvo,
                        sezione = dati_terreno.sezione,
                        immobile = safe_cast(dati_terreno.identificativo_immobile, int, None),
                        tipo_imm = dati_terreno.tipo_immobile,
                        progressiv = safe_cast(dati_terreno.progressivo, int, None),
                        foglio = safe_cast(dati_terreno.foglio, int, None),
                        numero = dati_terreno.numero,
                        denominato = safe_cast(dati_terreno.denominatore, int, None),
                        subalterno = dati_terreno.subalterno,
                        edificiale = dati_terreno.edificialita,
                        qualita = safe_cast(dati_terreno.qualita, int, None),
                        classe = dati_terreno.classe,
                        ettari = safe_cast(dati_terreno.ettari, int, None),
                        are = safe_cast(dati_terreno.are, int, None),
                        centiare = safe_cast(dati_terreno.centiare, int, None),
                        flag_redd = dati_terreno.flag_reddito,
                        flag_porz = dati_terreno.flag_porzione,
                        flag_deduz = dati_terreno.flag_deduzioni,
                        dominic_l = str(dati_terreno.reddito_dominicale_lire),
                        agrario_l = str(dati_terreno.reddito_agrario_lire),
                        dominic_e = str(dati_terreno.reddito_dominicale_euro),
                        agrario_e = str(dati_terreno.reddito_agrario_euro),
                        gen_eff = dati_terreno.data_di_efficacia00,
                        gen_regist = dati_terreno.data_di_registrazione00,
                        gen_tipo = dati_terreno.tipo_nota00,
                        gen_numero = dati_terreno.numero_nota00,
                        gen_progre = dati_terreno.progressivo_nota00,
                        gen_anno = safe_cast(dati_terreno.anno_nota00, int, None),
                        con_eff = None,
                        con_regist = None,
                        con_tipo = None,
                        con_numero = None,
                        con_progre = None,
                        con_anno = None,
                        partita = dati_terreno.partita,
                        annotazion = dati_terreno.annotazione,
                        mutaz_iniz = safe_cast(dati_terreno.identificativo_mutazione_iniziale, int, None),
                        mutaz_fine = safe_cast(dati_terreno.identificativo_mutazione_finale, int, None),
                        gen_causa = dati_terreno.codice_causale_atto_generante,
                        gen_descr = dati_terreno.descrizione_atto_generante,
                        con_causa = dati_terreno.codice_causale_atto_conclusivo,
                        con_descr = dati_terreno.descrizione_atto_conclusivo)


class Ctdeduzi(BaseModel):
    codice: str
    sezione: str
    immobile: int
    tipo_imm: str
    progressiv: int
    deduzione: str

    def extract_from_model(dati_terreno: TerreniRecordDue):
        return Ctdeduzi(codice = dati_terreno.codice_ammvo,
                        sezione = dati_terreno.sezione,
                        immobile = safe_cast(dati_terreno.identificativo_immobile, int, None),
                        tipo_imm = dati_terreno.tipo_immobile,
                        progressiv = safe_cast(dati_terreno.progressivo, int, None),
                        deduzione = dati_terreno.simbolo_deduzione)

class Ctriserv(BaseModel):
    codice: str
    sezione: str
    immobile: int
    tipo_imm: str
    progressiv: int
    riserva: str
    iscrizione: str

    def extract_from_model(dati_terreno: TerreniRecordTre):
        return Ctriserv(codice = dati_terreno.codice_ammvo,
                        sezione = dati_terreno.sezione,
                        immobile = safe_cast(dati_terreno.identificativo_immobile, int, None),
                        tipo_imm = dati_terreno.tipo_immobile,
                        progressiv = safe_cast(dati_terreno.progressivo, int, None),
                        riserva = dati_terreno.codice_riserva,
                        iscrizione = dati_terreno.partita_iscrizione_riserva)

class Ctporzio(BaseModel):
    codice: str
    sezione: str
    immobile: int
    tipo_imm: str
    progressiv: int
    porzione: str
    qualita: int
    classe: str
    ettari: int
    are: int
    centiare: int
    dominic_e: str
    agrario_e: str

    def extract_from_model(dati_terreno: TerreniRecordQuattroModel):
        return Ctporzio(codice = dati_terreno.codice_ammvo,
                        sezione = dati_terreno.sezione,
                        immobile = safe_cast(dati_terreno.identificativo_immobile, int, None),
                        tipo_imm = dati_terreno.tipo_immobile,
                        progressiv = safe_cast(dati_terreno.progressivo, int, None),
                        porzione = dati_terreno.identificativo_porzione,
                        qualita = safe_cast(dati_terreno.qualita, int, None),
                        classe = dati_terreno.classe,
                        ettari = safe_cast(dati_terreno.ettari, int, None),
                        are = safe_cast(dati_terreno.are, int, None),
                        centiare = safe_cast(dati_terreno.centiare, int, None),
                        dominic_e = None,
                        agrario_e = None)

class Cttitola(BaseModel):
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
        return Cttitola(codice = dati_titolarita.codice_ammvo,
                        sezione = dati_titolarita.sezione,
                        soggetto = safe_cast(dati_titolarita.identificativo_soggetto, int, None),
                        tipo_sog = dati_titolarita.tipo_soggetto,
                        immobile = safe_cast(dati_titolarita.identificativo_immobile, int, None),
                        tipo_imm = dati_titolarita.tipo_immobile,
                        diritto = dati_titolarita.codice_diritto,
                        titolo = dati_titolarita.titolo_non_codificato,
                        numeratore = safe_cast(dati_titolarita.quota_numeratore, int, None),
                        denominato = safe_cast(dati_titolarita.quota_denominatore, int, None),
                        regime = safe_cast(dati_titolarita.regime, int, None),
                        rif_regime = dati_titolarita.soggetto_di_riferimento,
                        gen_valida = dati_titolarita.data_di_validita00,
                        gen_nota = dati_titolarita.tipo_nota00,
                        gen_numero = dati_titolarita.numero_nota00,
                        gen_progre = dati_titolarita.progressivo_nota00,
                        gen_anno = dati_titolarita.anno_nota00,
                        gen_regist = dati_titolarita.data_registrazione_atti00,
                        partita = dati_titolarita.partita,
                        con_valida = dati_titolarita.data_di_validita99,
                        con_nota = dati_titolarita.tipo_nota99,
                        con_numero = dati_titolarita.numero_nota99,
                        con_progre = dati_titolarita.progressivo_nota99,
                        con_anno = dati_titolarita.anno_nota99,
                        con_regist = dati_titolarita.data_registrazione_atti99,
                        mutaz_iniz = safe_cast(dati_titolarita.identificativo_mutazione_iniziale, int, None),
                        mutaz_fine = safe_cast(dati_titolarita.identificativo_mutazione_finale, int, None),
                        identifica = safe_cast(dati_titolarita.identificativo_titolarita, int, None),
                        gen_causa = dati_titolarita.codice_causale_atto_generante,
                        gen_descr = dati_titolarita.descrizione_atto_generante,
                        con_causa = dati_titolarita.codice_causale_atto_conclusivo,
                        con_descr = dati_titolarita.descrizione_atto_conclusivo)

class Ctfisica(BaseModel):
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
        return Ctfisica(codice = dati_soggetto.codice_ammvo,
                        sezione = dati_soggetto.sezione,
                        soggetto = safe_cast(dati_soggetto.identificativo_soggetto, int, None),
                        tipo_sog = dati_soggetto.tipo_soggetto,
                        cognome = dati_soggetto.cognome,
                        nome = dati_soggetto.nome,
                        sesso = dati_soggetto.sesso,
                        data = dati_soggetto.data_di_nascita,
                        luogo = dati_soggetto.luogo_di_nascita,
                        codfiscale = dati_soggetto.codice_fiscale,
                        supplement = dati_soggetto.info_suppl)

class Ctnonfis(BaseModel):
    codice: str
    sezione: str
    soggetto: int
    tipo_sog: str
    codfiscale: str
    denominaz: str
    sede: str

    def extract_from_model(dati_soggetto: SoggettiModel):
        return Ctnonfis(codice = dati_soggetto.codice_ammvo,
                        sezione = dati_soggetto.sezione,
                        soggetto = safe_cast(dati_soggetto.identificativo_soggetto, int, None),
                        tipo_sog = dati_soggetto.tipo_soggetto,
                        codfiscale = dati_soggetto.codice_fiscale,
                        denominaz = dati_soggetto.denominazione,
                        sede = dati_soggetto.sede)

