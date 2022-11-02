from pydantic import BaseModel
from .building import (
    FabbricatiRecordUno, FabbricatiRecordTre, FabbricatiRecordQuattro, FabbricatiRecordCinque
)

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
                        immobile = dati_fabbricato.identificativo_immobile,
                        tipo_imm = dati_fabbricato.tipo_immobile,
                        progressiv = dati_fabbricato.progressivo,
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
                        mutaz_iniz = dati_fabbricato.identificativo_mutazione_iniziale,
                        mutaz_fine = dati_fabbricato.identificativo_mutazione_finale,
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
                        immobile = dati_fabbricato.identificativo_immobile,
                        tipo_imm = dati_fabbricato.tipo_immobile,
                        progressiv = dati_fabbricato.progressivo,
                        toponimo = dati_fabbricato.toponimo,
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
                        immobile = dati_fabbricato.identificativo_immobile,
                        tipo_imm = dati_fabbricato.tipo_immobile,
                        progressiv = dati_fabbricato.progressivo,
                        sez_urbana = dati_fabbricato.sezione_urbana,
                        foglio = dati_fabbricato.foglio,
                        numero = dati_fabbricato.numero,
                        denominato = dati_fabbricato.denominatore,
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
                        immobile = dati_fabbricato.identificativo_immobile,
                        tipo_imm = dati_fabbricato.tipo_immobile,
                        progressiv = dati_fabbricato.progressivo,
                        riserva = dati_fabbricato.codice_riserva,
                        iscrizione = dati_fabbricato.partita_iscrizione_riserva)