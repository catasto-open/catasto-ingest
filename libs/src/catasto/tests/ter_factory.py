import random
import string
from datetime import datetime, timedelta
from typing import Any, List

from catasto.schemas.land import (
    Deduzione,
    Porzione,
    PorzioneSdi,
    Riserva,
    TerreniImmobile,
    TerreniRecord1,
    TerreniRecord2,
    TerreniRecord3,
    TerreniRecord4,
)
from faker import Faker
from polyfactory.factories.pydantic_factory import ModelFactory

# Inizializzazione di Faker con impostazione locale italiana
fake = Faker(["it_IT"])
Faker.seed(42)  # Per riprodurre gli stessi dati casuali


class TerreniUtils:
    """Utility per la generazione di dati terreni specifici."""

    @staticmethod
    def genera_formato_data():
        """Genera una data casuale nel formato GGMMAAAA."""
        date = fake.date_between(start_date="-31y", end_date="-1y")
        if date.month > 12:
            # Nel caso improbabile che il mese sia > 12, lo correggiamo
            date = date.replace(month=date.month % 12 or 12)

        # Formatta la data nel formato richiesto GGMMAAAA
        return date.strftime("%d%m%Y")

    @staticmethod
    def genera_data_successiva(data_iniziale: str, min_days=1, max_days=365 * 5):
        """
        Genera una data successiva a quella fornita con un intervallo controllato.

        Args:
            data_iniziale (str): Data iniziale nel formato GGMMAAAA
            min_days (int): Numero minimo di giorni da aggiungere
            max_days (int): Numero massimo di giorni da aggiungere

        Returns:
            str: Data successiva nel formato GGMMAAAA
        """
        if not data_iniziale:
            return None

        # Converte la data da formato GGMMAAAA a oggetto datetime
        giorno, mese, anno = data_iniziale[:2], data_iniziale[2:4], data_iniziale[4:]
        data_dt = datetime(int(anno), int(mese), int(giorno))

        # Genera una data tra min_days e max_days dopo
        delta = random.randint(min_days, max_days)
        nuova_data = data_dt + timedelta(days=delta)

        return nuova_data.strftime("%d%m%Y")

    @staticmethod
    def genera_codice_amministrativo():
        """Genera un codice amministrativo di 4 cifre compatibile con Belfiore."""
        return f"{random.choices(string.ascii_uppercase, k=1)[0]}{random.randint(100, 999)}"

    @staticmethod
    def genera_foglio():
        """Genera un foglio casuale."""
        return str(random.randint(1, 9999)).zfill(4)

    @staticmethod
    def genera_numero(edificialita=None):
        """Genera un numero particella casuale."""
        if edificialita == "E":
            return f".{str(random.randint(1, 9999)).zfill(4)}"
        return str(random.randint(1, 99999)).zfill(5)

    @staticmethod
    def genera_denominatore():
        """Genera un denominatore casuale."""
        return str(random.randint(0, 9999)).zfill(4)

    @staticmethod
    def genera_subalterno():
        """Genera un subalterno casuale."""
        return str(random.randint(1, 9999)).zfill(4)

    @staticmethod
    def genera_edificialita():
        """Genera un flag edificialità casuale."""
        return random.choice(["E", " "])

    @staticmethod
    def genera_qualita():
        """Genera una qualità casuale."""
        return str(random.randint(100, 999))

    @staticmethod
    def genera_classe():
        """Genera una classe catastale casuale."""
        return str(random.randint(1, 10)).zfill(2)

    @staticmethod
    def genera_superficie():
        """Genera una superficie in ettari/are/centiare."""
        ettari = str(random.randint(0, 99999)).zfill(5)
        are = str(random.randint(0, 99)).zfill(2)
        centiare = str(random.randint(0, 99)).zfill(2)
        return (ettari, are, centiare)

    @staticmethod
    def genera_flag_reddito():
        """Genera un flag reddito casuale."""
        return random.choice(["0", "1", " "])

    @staticmethod
    def genera_flag_porzione():
        """Genera un flag porzione casuale."""
        return random.choice(["0", "1", " "])

    @staticmethod
    def genera_flag_deduzioni():
        """Genera un flag deduzioni casuale."""
        return random.choice(["0", "1", " "])

    @staticmethod
    def genera_reddito_lire():
        """Genera un reddito in lire casuale."""
        dom = str(random.randint(100, 999999999)).zfill(9)
        agr = str(random.randint(100, 99999999)).zfill(8)
        return (dom, agr)

    @staticmethod
    def genera_reddito_euro():
        """Genera un reddito in euro casuale."""
        dom = f"{random.randint(1, 99999)},{random.randint(1, 99)}"
        agr = f"{random.randint(1, 9999)},{random.randint(1, 99)}"
        return (dom, agr)

    @staticmethod
    def genera_tipo_nota():
        """Genera un tipo nota casuale."""
        return random.choice(["V", "I", "A"])

    @staticmethod
    def genera_numero_nota():
        """Genera un numero nota casuale."""
        return str(random.randint(1, 999999)).zfill(6)

    @staticmethod
    def genera_progressivo_nota():
        """Genera un progressivo nota casuale."""
        return str(random.randint(1, 999)).zfill(3)

    @staticmethod
    def genera_anno_nota():
        """Genera un anno nota casuale."""
        return str(random.randint(1990, 2022))

    @staticmethod
    def genera_partita():
        """Genera una partita casuale."""
        return str(random.randint(1, 9999999)).zfill(7)

    @staticmethod
    def genera_annotazione():
        """Genera un'annotazione casuale."""
        return fake.sentence(nb_words=10)[:200]

    @staticmethod
    def genera_identificativo_mutazione():
        """Genera un identificativo mutazione casuale."""
        return str(random.randint(100000000, 999999999))

    @staticmethod
    def genera_codice_causale():
        """Genera un codice causale casuale."""
        return str(random.randint(100, 999))

    @staticmethod
    def genera_descrizione_atto():
        """Genera una descrizione atto casuale."""
        return fake.sentence(nb_words=5)[:100]

    @staticmethod
    def genera_codice_riserva():
        """Genera un codice riserva casuale."""
        return random.choice(["A", "B", "C", "D", "E"])

    @staticmethod
    def genera_simbolo_deduzione():
        """Genera un simbolo deduzione casuale."""
        return f"{random.choice(string.ascii_uppercase)}{random.randint(1, 999):03d}"

    @staticmethod
    def genera_identificativo_porzione():
        """Genera un identificativo porzione casuale."""
        return random.choice(string.ascii_uppercase)


class DeduzioneFactory(ModelFactory[Deduzione]):
    """Factory per generare oggetti Deduzione."""

    __model__ = Deduzione

    @classmethod
    def build(cls, **kwargs) -> Deduzione:
        simbolo_deduzione = kwargs.get(
            "simbolo_deduzione", TerreniUtils.genera_simbolo_deduzione()
        )

        return Deduzione(
            simbolo_deduzione=simbolo_deduzione,
        )


class RiservaFactory(ModelFactory[Riserva]):
    """Factory per generare oggetti Riserva."""

    __model__ = Riserva

    @classmethod
    def build(cls, **kwargs) -> Riserva:
        codice_riserva = kwargs.get(
            "codice_riserva", TerreniUtils.genera_codice_riserva()
        )
        partita_iscrizione_riserva = kwargs.get(
            "partita_iscrizione_riserva", TerreniUtils.genera_partita()
        )

        return Riserva(
            codice_riserva=codice_riserva,
            partita_iscrizione_riserva=partita_iscrizione_riserva,
        )


class PorzioneFactory(ModelFactory[Porzione]):
    """Factory per generare oggetti Porzione."""

    __model__ = Porzione

    @classmethod
    def build(cls, **kwargs) -> Porzione:
        identificativo_porzione = kwargs.get(
            "identificativo_porzione", TerreniUtils.genera_identificativo_porzione()
        )
        qualita = kwargs.get("qualita", TerreniUtils.genera_qualita())
        classe = kwargs.get("classe", TerreniUtils.genera_classe())

        ettari, are, centiare = TerreniUtils.genera_superficie()

        return Porzione(
            identificativo_porzione=identificativo_porzione,
            qualita=qualita,
            classe=classe,
            ettari=ettari,
            are=are,
            centiare=centiare,
        )


class PorzioneSdiFactory(ModelFactory[PorzioneSdi]):
    """Factory per generare oggetti PorzioneSdi."""

    __model__ = PorzioneSdi

    @classmethod
    def build(cls, **kwargs) -> PorzioneSdi:
        porzione = PorzioneFactory.build(**kwargs)

        dom_euro, agr_euro = TerreniUtils.genera_reddito_euro()

        return PorzioneSdi(
            identificativo_porzione=porzione.identificativo_porzione,
            qualita=porzione.qualita,
            classe=porzione.classe,
            ettari=porzione.ettari,
            are=porzione.are,
            centiare=porzione.centiare,
            reddito_dominicale_euro=dom_euro,
            reddito_agrario_euro=agr_euro,
        )


class TerreniRecord1Factory(ModelFactory[TerreniRecord1]):
    """Factory per generare oggetti TerreniRecord1."""

    __model__ = TerreniRecord1

    @classmethod
    def build(cls, **kwargs) -> TerreniRecord1:
        """
        Genera un oggetto TerreniRecord1 con validazione rigorosa.

        Args:
            **kwargs: Parametri opzionali per personalizzare la generazione

        Returns:
            TerreniRecord1: Un'istanza validata del record
        """
        # Assicura campi obbligatori minimi
        codice_amministrativo = kwargs.get(
            "codice_amministrativo", TerreniUtils.genera_codice_amministrativo()
        )

        sezione = kwargs.get("sezione", random.choice(string.ascii_uppercase))

        identificativo_immobile = kwargs.get(
            "identificativo_immobile", str(random.randint(1000, 999999999))
        )

        progressivo = kwargs.get("progressivo", str(random.randint(1, 999)).zfill(3))

        # Elementi identificativi della particella
        edificialita = kwargs.get("edificialita", TerreniUtils.genera_edificialita())
        foglio = kwargs.get("foglio", TerreniUtils.genera_foglio())
        numero = kwargs.get("numero", TerreniUtils.genera_numero(edificialita))
        denominatore = kwargs.get("denominatore", TerreniUtils.genera_denominatore())
        subalterno = kwargs.get("subalterno", TerreniUtils.genera_subalterno())

        # Dati caratteristici della particella
        qualita = kwargs.get("qualita", TerreniUtils.genera_qualita())
        classe = kwargs.get("classe", TerreniUtils.genera_classe())

        ettari, are, centiare = TerreniUtils.genera_superficie()

        # Flag e redditi
        flag_reddito = kwargs.get("flag_reddito", TerreniUtils.genera_flag_reddito())
        flag_porzione = kwargs.get("flag_porzione", TerreniUtils.genera_flag_porzione())
        flag_deduzioni = kwargs.get(
            "flag_deduzioni", TerreniUtils.genera_flag_deduzioni()
        )

        reddito_dominicale_lire, reddito_agrario_lire = (
            TerreniUtils.genera_reddito_lire()
        )
        reddito_dominicale_euro, reddito_agrario_euro = (
            TerreniUtils.genera_reddito_euro()
        )

        # Date
        data_efficacia_iniziale = kwargs.get(
            "data_efficacia_iniziale", TerreniUtils.genera_formato_data()
        )

        data_registrazione_atti_iniziale = kwargs.get(
            "data_registrazione_atti_iniziale", TerreniUtils.genera_formato_data()
        )

        # Genera tipo_nota e altri dati per la situazione iniziale
        tipo_nota_iniziale = kwargs.get(
            "tipo_nota_iniziale", TerreniUtils.genera_tipo_nota()
        )
        numero_nota_iniziale = kwargs.get(
            "numero_nota_iniziale", TerreniUtils.genera_numero_nota()
        )
        progressivo_nota_iniziale = kwargs.get(
            "progressivo_nota_iniziale", TerreniUtils.genera_progressivo_nota()
        )
        anno_nota_iniziale = kwargs.get(
            "anno_nota_iniziale", TerreniUtils.genera_anno_nota()
        )

        # Prepara il dizionario con i campi minimi richiesti
        data = {
            "codice_amministrativo": codice_amministrativo,
            "sezione": sezione,
            "identificativo_immobile": identificativo_immobile,
            "tipo_immobile": "T",
            "progressivo": progressivo,
            "tipo_record": "1",
            "foglio": foglio,
            "numero": numero,
            "denominatore": denominatore,
            "subalterno": subalterno,
            "edificialita": edificialita,
            "qualita": qualita,
            "classe": classe,
            "ettari": ettari,
            "are": are,
            "centiare": centiare,
            "flag_reddito": flag_reddito,
            "flag_porzione": flag_porzione,
            "flag_deduzioni": flag_deduzioni,
            "reddito_dominicale_lire": reddito_dominicale_lire,
            "reddito_agrario_lire": reddito_agrario_lire,
            "reddito_dominicale_euro": reddito_dominicale_euro,
            "reddito_agrario_euro": reddito_agrario_euro,
            "data_efficacia_iniziale": data_efficacia_iniziale,
            "data_registrazione_atti_iniziale": data_registrazione_atti_iniziale,
            "tipo_nota_iniziale": tipo_nota_iniziale,
            "numero_nota_iniziale": numero_nota_iniziale,
            "progressivo_nota_iniziale": progressivo_nota_iniziale,
            "anno_nota_iniziale": anno_nota_iniziale,
        }

        # Flag per generare dati finali (30% di probabilità)
        genera_dati_finali = random.random() > 0.7

        # Aggiungi campi opzionali
        partita = kwargs.get("partita", TerreniUtils.genera_partita())
        if partita:
            data["partita"] = partita

        annotazione = kwargs.get(
            "annotazione",
            TerreniUtils.genera_annotazione() if random.random() > 0.8 else None,
        )
        if annotazione:
            data["annotazione"] = annotazione

        identificativo_mutazione_iniziale = kwargs.get(
            "identificativo_mutazione_iniziale",
            TerreniUtils.genera_identificativo_mutazione(),
        )
        if identificativo_mutazione_iniziale:
            data["identificativo_mutazione_iniziale"] = (
                identificativo_mutazione_iniziale
            )

        codice_causale_atto_generante = kwargs.get(
            "codice_causale_atto_generante", TerreniUtils.genera_codice_causale()
        )
        if codice_causale_atto_generante:
            data["codice_causale_atto_generante"] = codice_causale_atto_generante

        descrizione_atto_generante = kwargs.get(
            "descrizione_atto_generante", TerreniUtils.genera_descrizione_atto()
        )
        if descrizione_atto_generante:
            data["descrizione_atto_generante"] = descrizione_atto_generante

        # Aggiungi dati finali se necessario
        if genera_dati_finali:
            data_efficacia_finale = kwargs.get(
                "data_efficacia_finale",
                TerreniUtils.genera_data_successiva(data_efficacia_iniziale),
            )
            if data_efficacia_finale:
                data["data_efficacia_finale"] = data_efficacia_finale

            data_registrazione_atti_finale = kwargs.get(
                "data_registrazione_atti_finale",
                TerreniUtils.genera_data_successiva(data_registrazione_atti_iniziale),
            )
            if data_registrazione_atti_finale:
                data["data_registrazione_atti_finale"] = data_registrazione_atti_finale

            tipo_nota_finale = kwargs.get(
                "tipo_nota_finale", TerreniUtils.genera_tipo_nota()
            )
            if tipo_nota_finale:
                data["tipo_nota_finale"] = tipo_nota_finale

            numero_nota_finale = kwargs.get(
                "numero_nota_finale", TerreniUtils.genera_numero_nota()
            )
            if numero_nota_finale:
                data["numero_nota_finale"] = numero_nota_finale

            progressivo_nota_finale = kwargs.get(
                "progressivo_nota_finale", TerreniUtils.genera_progressivo_nota()
            )
            if progressivo_nota_finale:
                data["progressivo_nota_finale"] = progressivo_nota_finale

            anno_nota_finale = kwargs.get(
                "anno_nota_finale", TerreniUtils.genera_anno_nota()
            )
            if anno_nota_finale:
                data["anno_nota_finale"] = anno_nota_finale

            identificativo_mutazione_finale = kwargs.get(
                "identificativo_mutazione_finale",
                TerreniUtils.genera_identificativo_mutazione(),
            )
            if identificativo_mutazione_finale:
                data["identificativo_mutazione_finale"] = (
                    identificativo_mutazione_finale
                )

            codice_causale_atto_conclusivo = kwargs.get(
                "codice_causale_atto_conclusivo", TerreniUtils.genera_codice_causale()
            )
            if codice_causale_atto_conclusivo:
                data["codice_causale_atto_conclusivo"] = codice_causale_atto_conclusivo

            descrizione_atto_conclusivo = kwargs.get(
                "descrizione_atto_conclusivo", TerreniUtils.genera_descrizione_atto()
            )
            if descrizione_atto_conclusivo:
                data["descrizione_atto_conclusivo"] = descrizione_atto_conclusivo

        # Costruisci e valida l'oggetto
        return TerreniRecord1(**data)


class TerreniRecord2Factory(ModelFactory[TerreniRecord2]):
    """Factory per generare oggetti TerreniRecord2."""

    __model__ = TerreniRecord2

    @classmethod
    def build(cls, **kwargs) -> TerreniRecord2:
        # Dati di base
        codice_amministrativo = kwargs.get(
            "codice_amministrativo", TerreniUtils.genera_codice_amministrativo()
        )
        sezione = kwargs.get("sezione", random.choice(string.ascii_uppercase))
        identificativo_immobile = kwargs.get(
            "identificativo_immobile", str(random.randint(1000, 999999999))
        )
        progressivo = kwargs.get("progressivo", str(random.randint(1, 999)).zfill(3))

        # Genera deduzioni
        num_deduzioni = kwargs.get("num_deduzioni", random.randint(1, 3))
        deduzioni = kwargs.get(
            "deduzioni",
            [DeduzioneFactory.build() for _ in range(min(num_deduzioni, 7))],
        )

        return TerreniRecord2(
            codice_amministrativo=codice_amministrativo,
            sezione=sezione,
            identificativo_immobile=identificativo_immobile,
            tipo_immobile="T",
            progressivo=progressivo,
            tipo_record="2",
            deduzioni=deduzioni,
        )


class TerreniRecord3Factory(ModelFactory[TerreniRecord3]):
    """Factory per generare oggetti TerreniRecord3."""

    __model__ = TerreniRecord3

    @classmethod
    def build(cls, **kwargs) -> TerreniRecord3:
        # Dati di base
        codice_amministrativo = kwargs.get(
            "codice_amministrativo", TerreniUtils.genera_codice_amministrativo()
        )
        sezione = kwargs.get("sezione", random.choice(string.ascii_uppercase))
        identificativo_immobile = kwargs.get(
            "identificativo_immobile", str(random.randint(1000, 999999999))
        )
        progressivo = kwargs.get("progressivo", str(random.randint(1, 999)).zfill(3))

        # Genera riserve
        num_riserve = kwargs.get("num_riserve", random.randint(1, 3))
        riserve = kwargs.get(
            "riserve",
            [RiservaFactory.build() for _ in range(min(num_riserve, 10))],
        )

        return TerreniRecord3(
            codice_amministrativo=codice_amministrativo,
            sezione=sezione,
            identificativo_immobile=identificativo_immobile,
            tipo_immobile="T",
            progressivo=progressivo,
            tipo_record="3",
            riserve=riserve,
        )


class TerreniRecord4Factory(ModelFactory[TerreniRecord4]):
    """Factory per generare oggetti TerreniRecord4."""

    __model__ = TerreniRecord4

    @classmethod
    def build(cls, **kwargs) -> TerreniRecord4:
        # Dati di base
        codice_amministrativo = kwargs.get(
            "codice_amministrativo", TerreniUtils.genera_codice_amministrativo()
        )
        sezione = kwargs.get("sezione", random.choice(string.ascii_uppercase))
        identificativo_immobile = kwargs.get(
            "identificativo_immobile", str(random.randint(1000, 999999999))
        )
        progressivo = kwargs.get("progressivo", str(random.randint(1, 999)).zfill(3))

        # Scelta se usare Porzione o PorzioneSdi (50% di probabilità per ciascuno)
        usa_sdi = (
            True  # random.random() > 0.5  # forzo sempre Sdi per validare solo Smidt
        )

        # Genera porzioni
        num_porzioni = kwargs.get("num_porzioni", random.randint(1, 3))
        if usa_sdi:
            porzioni = kwargs.get(
                "porzioni",
                [PorzioneSdiFactory.build() for _ in range(min(num_porzioni, 20))],
            )
        else:
            porzioni = kwargs.get(
                "porzioni",
                [PorzioneFactory.build() for _ in range(min(num_porzioni, 20))],
            )

        return TerreniRecord4(
            codice_amministrativo=codice_amministrativo,
            sezione=sezione,
            identificativo_immobile=identificativo_immobile,
            tipo_immobile="T",
            progressivo=progressivo,
            tipo_record="4",
            porzioni=porzioni,
        )


class TerreniImmobileFactory(ModelFactory[TerreniImmobile]):
    """Factory per generare oggetti TerreniImmobile."""

    __model__ = TerreniImmobile

    @classmethod
    def build(cls, **kwargs) -> TerreniImmobile:
        """Genera un immobile completo con tutti i record necessari."""
        # Genera i dati comuni
        codice_amministrativo = kwargs.get(
            "codice_amministrativo", TerreniUtils.genera_codice_amministrativo()
        )
        sezione = kwargs.get("sezione", random.choice(string.ascii_uppercase))
        identificativo_immobile = kwargs.get(
            "identificativo_immobile", str(random.randint(1000, 999999999))
        )
        progressivo = kwargs.get("progressivo", str(random.randint(1, 999)).zfill(3))

        # Genera record1 (obbligatorio)
        record1 = kwargs.get(
            "record1",
            TerreniRecord1Factory.build(
                codice_amministrativo=codice_amministrativo,
                sezione=sezione,
                identificativo_immobile=identificativo_immobile,
                progressivo=progressivo,
            ),
        )

        # Genera record2 (obbligatorio se flag_deduzioni = 1)
        record2 = kwargs.get("record2")
        if record2 is None and record1.flag_deduzioni == "1":
            record2 = TerreniRecord2Factory.build(
                codice_amministrativo=codice_amministrativo,
                sezione=sezione,
                identificativo_immobile=identificativo_immobile,
                progressivo=progressivo,
            )

        # Record opzionali
        record3 = kwargs.get("record3")
        if (
            record3 is None and random.random() > 0.7
        ):  # 30% di probabilità di avere record3
            record3 = TerreniRecord3Factory.build(
                codice_amministrativo=codice_amministrativo,
                sezione=sezione,
                identificativo_immobile=identificativo_immobile,
                progressivo=progressivo,
            )

        record4 = kwargs.get("record4")
        if (
            record4 is None and record1.flag_porzione == "1"
        ):  # Se flag_porzione = 1, deve avere record4
            record4 = TerreniRecord4Factory.build(
                codice_amministrativo=codice_amministrativo,
                sezione=sezione,
                identificativo_immobile=identificativo_immobile,
                progressivo=progressivo,
            )

        # Crea e restituisce l'oggetto immobile
        return TerreniImmobile(
            codice_amministrativo=codice_amministrativo,
            sezione=sezione,
            identificativo_immobile=identificativo_immobile,
            tipo_immobile="T",
            progressivo=progressivo,
            record1=record1,
            record2=record2,
            record3=record3,
            record4=record4,
        )


class TerreniTestGenerator:
    """Classe per generare dati di test per i file TER."""

    @staticmethod
    def genera_immobile_completo() -> List[Any]:
        """
        Genera un set completo di record per un immobile.

        Returns:
            List: Lista di oggetti record
        """
        immobile = TerreniImmobileFactory.build()

        # Raccogli tutti i record in una lista
        records = [immobile.record1]
        if immobile.record2:
            records.append(immobile.record2)
        if immobile.record3:
            records.append(immobile.record3)
        if immobile.record4:
            records.append(immobile.record4)

        return records

    @staticmethod
    def genera_file_terreni(num_immobili: int = 5) -> List[Any]:
        """
        Genera un file terreni completo.

        Args:
            num_immobili: Numero di immobili da generare

        Returns:
            List: Lista di oggetti record
        """
        all_records = []

        for _ in range(num_immobili):
            records = TerreniTestGenerator.genera_immobile_completo()
            all_records.extend(records)

        return all_records

    @staticmethod
    def genera_file_content(records: List[Any]) -> str:
        """
        Converte i record in contenuto del file TER.

        Args:
            records: Lista di oggetti record

        Returns:
            str: Contenuto del file TER
        """
        lines = []

        for record in records:
            line = TerreniTestGenerator._record_to_line(record)
            lines.append(line)

        return "\n".join(lines)

    @staticmethod
    def _record_to_line(record: Any) -> str:
        """
        Converte un record in una linea del file TER.

        Args:
            record: L'oggetto record da convertire

        Returns:
            str: La linea del file TER
        """
        # Parte campi comuni a tutti
        header = f"{record.codice_amministrativo}|{record.sezione}|{record.identificativo_immobile}|{record.tipo_immobile}|{record.progressivo}|{record.tipo_record}"

        # Inizia la parte dati
        data = ""

        # Aggiungi campi specifici in base al tipo di record
        try:
            if record.tipo_record == "1":
                # Formatta i campi per il record di tipo 1
                data_parts = [
                    record.foglio,
                    record.numero,
                    record.denominatore,
                    record.subalterno,
                    record.edificialita,
                    record.qualita,
                    record.classe,
                    record.ettari,
                    record.are,
                    record.centiare,
                    record.flag_reddito or "",
                    record.flag_porzione or "",
                    record.flag_deduzioni or "",
                    record.reddito_dominicale_lire or "",
                    record.reddito_agrario_lire or "",
                    record.reddito_dominicale_euro or "",
                    record.reddito_agrario_euro or "",
                    record.data_efficacia_iniziale,
                    record.data_registrazione_atti_iniziale,
                    record.tipo_nota_iniziale,
                    record.numero_nota_iniziale,
                    record.progressivo_nota_iniziale,
                    record.anno_nota_iniziale,
                    record.data_efficacia_finale or "",
                    record.data_registrazione_atti_finale or "",
                    record.tipo_nota_finale or "",
                    record.numero_nota_finale or "",
                    record.progressivo_nota_finale or "",
                    record.anno_nota_finale or "",
                    record.partita or "",
                    record.annotazione or "",
                    record.identificativo_mutazione_iniziale or "",
                    record.identificativo_mutazione_finale or "",
                    record.codice_causale_atto_generante or "",
                    record.descrizione_atto_generante or "",
                    record.codice_causale_atto_conclusivo or "",
                    record.descrizione_atto_conclusivo or "",
                ]
                data += "|".join(data_parts)

            elif record.tipo_record == "2":
                # Formatta le deduzioni per il record di tipo 2
                deduzioni_parts = []
                for deduzione in record.deduzioni:
                    deduzioni_parts.append(deduzione.simbolo_deduzione)

                data += "|".join(deduzioni_parts)

            elif record.tipo_record == "3":
                # Formatta le riserve per il record di tipo 3
                riserve_parts = []
                for riserva in record.riserve:
                    riserva_part = f"{riserva.codice_riserva}|{riserva.partita_iscrizione_riserva or ''}"
                    riserve_parts.append(riserva_part)

                data += "|".join(riserve_parts)

            elif record.tipo_record == "4":
                # Formatta le porzioni per il record di tipo 4
                porzioni_parts = []
                for porzione in record.porzioni:
                    # Controlla se è una PorzioneSdi che ha i redditi in euro
                    if hasattr(porzione, "reddito_dominicale_euro"):
                        porzione_part = f"{porzione.identificativo_porzione}|{porzione.qualita}|{porzione.classe}|{porzione.ettari}|{porzione.are}|{porzione.centiare}|{porzione.reddito_dominicale_euro or ''}|{porzione.reddito_agrario_euro or ''}"
                    else:
                        porzione_part = f"{porzione.identificativo_porzione}|{porzione.qualita}|{porzione.classe}|{porzione.ettari}|{porzione.are}|{porzione.centiare}"
                    porzioni_parts.append(porzione_part)

                data += "|".join(porzioni_parts)

            return f"{header}|{data}"
        except Exception as e:
            print(f"Errore nella conversione del record a linea: {e}")
            raise
