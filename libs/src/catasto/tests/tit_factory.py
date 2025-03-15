import random
import string
from datetime import datetime, timedelta
from typing import List

from catasto.schemas.entitlement import (
    TipoImmobileEnum,
    TipoRegimeEnum,
    TipoSoggettoEnum,
    Titolarita,
    TitolaritaModel,
)
from faker import Faker
from polyfactory.factories.pydantic_factory import ModelFactory

# Inizializzazione di Faker con impostazione locale italiana
fake = Faker(["it_IT"])
Faker.seed(42)  # Per riprodurre gli stessi dati casuali


class TitolaritaUtils:
    """Utility per la generazione di dati di titolarità specifici."""

    @staticmethod
    def genera_formato_data():
        """Genera una data casuale nel formato GGMMAAAA."""
        date = fake.date_between(start_date="-10y", end_date="-1d")
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
            str: Data successiva nel formato GGMMAAAA o None se random > 0.7
        """
        if (
            not data_iniziale or random.random() > 0.3
        ):  # 30% probabilità di avere una data fine
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
    def genera_identificativo_soggetto():
        """Genera un identificativo soggetto casuale."""
        return str(random.randint(1000, 999999999))

    @staticmethod
    def genera_identificativo_immobile():
        """Genera un identificativo immobile casuale."""
        return str(random.randint(1000, 999999999))

    @staticmethod
    def genera_tipo_soggetto():
        """Genera un tipo soggetto casuale."""
        return random.choice([item.value for item in TipoSoggettoEnum])

    @staticmethod
    def genera_tipo_immobile():
        """Genera un tipo immobile casuale."""
        return random.choice([item.value for item in TipoImmobileEnum])

    @staticmethod
    def genera_quota():
        """Genera una coppia numeratore/denominatore casuale per la quota."""
        denominatore = random.choice([1, 2, 4, 5, 8, 10, 100, 1000])
        numeratore = random.randint(1, denominatore)
        return str(numeratore), str(denominatore)

    @staticmethod
    def genera_regime():
        """Genera un regime casuale."""
        return random.choice([item.value for item in TipoRegimeEnum])

    @staticmethod
    def genera_codice_diritto():
        """Genera un codice diritto casuale."""
        # Codici diritto comuni (esempio)
        codici = ["1", "2", "3", "10", "20", "30", "100", "P", "U"]
        return random.choice(codici)

    @staticmethod
    def genera_titolo_non_codificato():
        """Genera un titolo non codificato casuale."""
        return fake.sentence(nb_words=3)[:100] if random.random() > 0.7 else None

    @staticmethod
    def genera_tipo_nota():
        """Genera un tipo nota casuale."""
        return random.choice(["V", "I", "A"])

    @staticmethod
    def genera_numero_nota():
        """Genera un numero nota casuale."""
        return str(random.randint(1, 999999))

    @staticmethod
    def genera_progressivo_nota():
        """Genera un progressivo nota casuale."""
        return str(random.randint(1, 999))

    @staticmethod
    def genera_anno_nota():
        """Genera un anno nota casuale."""
        return str(random.randint(1990, 2022))

    @staticmethod
    def genera_partita():
        """Genera una partita casuale."""
        return str(random.randint(1, 9999999))

    @staticmethod
    def genera_identificativo_mutazione():
        """Genera un identificativo mutazione casuale."""
        return str(random.randint(1, 999999999))

    @staticmethod
    def genera_identificativo_titolarita():
        """Genera un identificativo titolarità casuale."""
        return str(random.randint(1, 999999999))

    @staticmethod
    def genera_codice_causale():
        """Genera un codice causale casuale."""
        return str(random.randint(1, 999))

    @staticmethod
    def genera_descrizione_atto():
        """Genera una descrizione atto casuale."""
        return fake.sentence(nb_words=5)[:100] if random.random() > 0.5 else None


class TitolaritaFactory(ModelFactory[Titolarita]):
    """Factory per generare oggetti Titolarita."""

    __model__ = Titolarita

    @classmethod
    def build(cls, **kwargs) -> Titolarita:
        """
        Genera un oggetto Titolarita con validazione rigorosa.

        Args:
            **kwargs: Parametri opzionali per personalizzare la generazione

        Returns:
            Titolarita: Un'istanza validata del record
        """
        # Assicura campi obbligatori minimi
        codice_amministrativo = kwargs.get(
            "codice_amministrativo", TitolaritaUtils.genera_codice_amministrativo()
        )

        sezione = kwargs.get("sezione", random.choice(string.ascii_uppercase))

        identificativo_soggetto = kwargs.get(
            "identificativo_soggetto", TitolaritaUtils.genera_identificativo_soggetto()
        )

        tipo_soggetto = kwargs.get(
            "tipo_soggetto", TitolaritaUtils.genera_tipo_soggetto()
        )

        identificativo_immobile = kwargs.get(
            "identificativo_immobile", TitolaritaUtils.genera_identificativo_immobile()
        )

        tipo_immobile = kwargs.get(
            "tipo_immobile", TitolaritaUtils.genera_tipo_immobile()
        )

        # Genera i dati della titolarità
        codice_diritto = kwargs.get(
            "codice_diritto", TitolaritaUtils.genera_codice_diritto()
        )
        titolo_non_codificato = kwargs.get(
            "titolo_non_codificato", TitolaritaUtils.genera_titolo_non_codificato()
        )

        numeratore, denominatore = TitolaritaUtils.genera_quota()
        quota_numeratore = kwargs.get("quota_numeratore", numeratore)
        quota_denominatore = kwargs.get("quota_denominatore", denominatore)

        regime = kwargs.get("regime", TitolaritaUtils.genera_regime())
        soggetto_di_riferimento = kwargs.get(
            "soggetto_di_riferimento", TitolaritaUtils.genera_identificativo_soggetto()
        )

        data_di_validita_iniziale = kwargs.get(
            "data_di_validita_iniziale", TitolaritaUtils.genera_formato_data()
        )

        tipo_nota_iniziale = kwargs.get(
            "tipo_nota_iniziale", TitolaritaUtils.genera_tipo_nota()
        )
        numero_nota_iniziale = kwargs.get(
            "numero_nota_iniziale", TitolaritaUtils.genera_numero_nota()
        )
        progressivo_nota_iniziale = kwargs.get(
            "progressivo_nota_iniziale", TitolaritaUtils.genera_progressivo_nota()
        )
        anno_nota_iniziale = kwargs.get(
            "anno_nota_iniziale", TitolaritaUtils.genera_anno_nota()
        )

        data_registrazione_atti_iniziale = kwargs.get(
            "data_registrazione_atti_iniziale", TitolaritaUtils.genera_formato_data()
        )

        partita = kwargs.get("partita", TitolaritaUtils.genera_partita())

        data_di_validita_finale = kwargs.get(
            "data_di_validita_finale",
            TitolaritaUtils.genera_data_successiva(data_di_validita_iniziale),
        )

        tipo_nota_finale = kwargs.get(
            "tipo_nota_finale", TitolaritaUtils.genera_tipo_nota()
        )
        numero_nota_finale = kwargs.get(
            "numero_nota_finale", TitolaritaUtils.genera_numero_nota()
        )
        progressivo_nota_finale = kwargs.get(
            "progressivo_nota_finale", TitolaritaUtils.genera_progressivo_nota()
        )
        anno_nota_finale = kwargs.get(
            "anno_nota_finale", TitolaritaUtils.genera_anno_nota()
        )

        data_registrazione_atti_finale = kwargs.get(
            "data_registrazione_atti_finale",
            TitolaritaUtils.genera_data_successiva(data_registrazione_atti_iniziale),
        )

        identificativo_mutazione_iniziale = kwargs.get(
            "identificativo_mutazione_iniziale",
            TitolaritaUtils.genera_identificativo_mutazione(),
        )

        identificativo_mutazione_finale = kwargs.get(
            "identificativo_mutazione_finale",
            TitolaritaUtils.genera_identificativo_mutazione()
            if data_di_validita_finale
            else None,
        )

        identificativo_titolarita = kwargs.get(
            "identificativo_titolarita",
            TitolaritaUtils.genera_identificativo_titolarita(),
        )

        codice_causale_atto_generante = kwargs.get(
            "codice_causale_atto_generante", TitolaritaUtils.genera_codice_causale()
        )

        descrizione_atto_generante = kwargs.get(
            "descrizione_atto_generante", TitolaritaUtils.genera_descrizione_atto()
        )

        codice_causale_atto_conclusivo = kwargs.get(
            "codice_causale_atto_conclusivo",
            TitolaritaUtils.genera_codice_causale()
            if data_di_validita_finale
            else None,
        )

        descrizione_atto_conclusivo = kwargs.get(
            "descrizione_atto_conclusivo",
            TitolaritaUtils.genera_descrizione_atto()
            if data_di_validita_finale
            else None,
        )

        # Prepara il dizionario con i campi richiesti
        data = {
            "codice_amministrativo": codice_amministrativo,
            "sezione": sezione,
            "identificativo_soggetto": identificativo_soggetto,
            "tipo_soggetto": TipoSoggettoEnum(tipo_soggetto),
            "identificativo_immobile": identificativo_immobile,
            "tipo_immobile": TipoImmobileEnum(tipo_immobile),
            "codice_diritto": codice_diritto,
            "quota_numeratore": quota_numeratore,
            "quota_denominatore": quota_denominatore,
            "regime": TipoRegimeEnum(regime),
            "soggetto_di_riferimento": soggetto_di_riferimento,
            "tipo_nota_iniziale": tipo_nota_iniziale,
            "numero_nota_iniziale": numero_nota_iniziale,
            "progressivo_nota_iniziale": progressivo_nota_iniziale,
            "anno_nota_iniziale": anno_nota_iniziale,
            "identificativo_titolarita": identificativo_titolarita,
        }

        # Aggiungi campi opzionali se presenti
        if titolo_non_codificato:
            data["titolo_non_codificato"] = titolo_non_codificato

        if data_di_validita_iniziale:
            data["data_di_validita_iniziale"] = data_di_validita_iniziale

        if data_registrazione_atti_iniziale:
            data["data_registrazione_atti_iniziale"] = data_registrazione_atti_iniziale

        if partita:
            data["partita"] = partita

        if data_di_validita_finale:
            data["data_di_validita_finale"] = data_di_validita_finale

        if data_registrazione_atti_finale:
            data["data_registrazione_atti_finale"] = data_registrazione_atti_finale

        if identificativo_mutazione_iniziale:
            data["identificativo_mutazione_iniziale"] = (
                identificativo_mutazione_iniziale
            )

        if identificativo_mutazione_finale:
            data["identificativo_mutazione_finale"] = identificativo_mutazione_finale

        if codice_causale_atto_generante:
            data["codice_causale_atto_generante"] = codice_causale_atto_generante

        if descrizione_atto_generante:
            data["descrizione_atto_generante"] = descrizione_atto_generante

        if codice_causale_atto_conclusivo:
            data["codice_causale_atto_conclusivo"] = codice_causale_atto_conclusivo

        if descrizione_atto_conclusivo:
            data["descrizione_atto_conclusivo"] = descrizione_atto_conclusivo

        # Costruisci e valida l'oggetto
        return Titolarita(**data)


class TitolaritaModelFactory(ModelFactory[TitolaritaModel]):
    """Factory per generare oggetti TitolaritaModel."""

    __model__ = TitolaritaModel

    @classmethod
    def build(cls, num_titolarita=5, **kwargs) -> TitolaritaModel:
        """
        Genera un modello TitolaritaModel popolato.

        Args:
            num_titolarita: Numero di titolarità da generare
            **kwargs: Altri parametri opzionali

        Returns:
            TitolaritaModel: Un'istanza del modello con titolarità generate
        """
        model = TitolaritaModel()

        for _ in range(num_titolarita):
            titolarita = TitolaritaFactory.build()
            model.add_titolarita(titolarita)

        return model


class TitolaritaTestGenerator:
    """Classe per generare dati di test per i file TIT."""

    @staticmethod
    def genera_file_titolarita(num_titolarita: int = 5) -> List[Titolarita]:
        """
        Genera un file titolarità completo.

        Args:
            num_titolarita: Numero di titolarità da generare

        Returns:
            List: Lista di oggetti Titolarita
        """
        all_records = []

        for _ in range(num_titolarita):
            titolarita = TitolaritaFactory.build()
            all_records.append(titolarita)

        return all_records

    @staticmethod
    def genera_file_content(records: List[Titolarita]) -> str:
        """
        Converte i record in contenuto del file TIT.

        Args:
            records: Lista di oggetti Titolarita

        Returns:
            str: Contenuto del file TIT
        """
        lines = []

        for record in records:
            line = TitolaritaTestGenerator._record_to_line(record)
            lines.append(line)

        return "\n".join(lines)

    @staticmethod
    def _record_to_line(
        record: Titolarita,
    ) -> str:
        """
        Converte un record in una linea del file TIT.

        Args:
            record: L'oggetto record da convertire

        Returns:
            str: La linea del file TIT
        """
        # Parte campi comuni a tutti
        header = f"{record.codice_amministrativo}|{record.sezione}|{record.identificativo_soggetto}|{record.tipo_soggetto}|{record.identificativo_immobile}|{record.tipo_immobile}"

        # Formatta i campi per la titolarità
        data_parts = [
            record.codice_diritto,
            record.titolo_non_codificato or "",
            record.quota_numeratore,
            record.quota_denominatore,
            record.regime if record.regime else "",
            record.soggetto_di_riferimento,
            record.data_di_validita_iniziale or "",
            record.tipo_nota_iniziale,
            record.numero_nota_iniziale,
            record.progressivo_nota_iniziale,
            record.anno_nota_iniziale,
            record.data_registrazione_atti_iniziale or "",
            record.partita or "",
            record.data_di_validita_finale or "",
            record.tipo_nota_finale or "",
            record.numero_nota_finale or "",
            record.progressivo_nota_finale or "",
            record.anno_nota_finale or "",
            record.data_registrazione_atti_finale or "",
            record.identificativo_mutazione_iniziale or "",
            record.identificativo_mutazione_finale or "",
            record.identificativo_titolarita,
            record.codice_causale_atto_generante or "",
            record.descrizione_atto_generante or "",
            record.codice_causale_atto_conclusivo or "",
            record.descrizione_atto_conclusivo or "",
        ]
        data = "|".join(data_parts)

        return f"{header}|{data}"
