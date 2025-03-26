import random
import string
from typing import Any, List, Union

from catasto.schemas.subject import (
    SessoEnum,
    SoggettiRecordGiuridicPerson,
    SoggettiRecordPrivatePerson,
    Soggetto,
    TipoSoggettoEnum,
)
from faker import Faker
from polyfactory.factories.pydantic_factory import ModelFactory

# Inizializzazione di Faker con impostazione locale italiana
fake = Faker(["it_IT"])
Faker.seed(42)  # Per riprodurre gli stessi dati casuali


class SoggettiUtils:
    """Utility per la generazione di dati soggetti specifici."""

    @staticmethod
    def genera_formato_data():
        """Genera una data casuale nel formato GGMMAAAA."""
        date = fake.date_between(start_date="-80y", end_date="-18y")
        if date.month > 12:
            # Nel caso improbabile che il mese sia > 12, lo correggiamo
            date = date.replace(month=date.month % 12 or 12)

        # Formatta la data nel formato richiesto GGMMAAAA
        return date.strftime("%d%m%Y")

    @staticmethod
    def genera_codice_amministrativo():
        """Genera un codice amministrativo di 4 cifre compatibile con Belfiore."""
        return f"{random.choices(string.ascii_uppercase, k=1)[0]}{random.randint(100, 999)}"

    @staticmethod
    def genera_codice_fiscale_persona():
        """Genera un codice fiscale valido per una persona fisica."""
        return fake.ssn()  # In Italia, fake.ssn() genera un codice fiscale valido

    @staticmethod
    def genera_codice_fiscale_azienda():
        """Genera un codice fiscale/partita IVA valido per una persona giuridica."""
        # Le partite IVA italiane sono di 11 cifre
        return "".join([str(random.randint(0, 9)) for _ in range(11)])

    @staticmethod
    def genera_luogo_nascita():
        """Genera un codice comune valido per il luogo di nascita."""
        # Usa lo stesso formato del codice amministrativo
        return SoggettiUtils.genera_codice_amministrativo()


class SoggettiRecordPrivatePersonFactory(ModelFactory[SoggettiRecordPrivatePerson]):
    """Factory per generare oggetti SoggettiRecordPrivatePerson."""

    __model__ = SoggettiRecordPrivatePerson

    @classmethod
    def build(cls, **kwargs) -> SoggettiRecordPrivatePerson:
        """
        Genera un oggetto SoggettiRecordPrivatePerson con validazione rigorosa.

        Args:
            **kwargs: Parametri opzionali per personalizzare la generazione

        Returns:
            SoggettiRecordPrivatePerson: Un'istanza validata del record
        """
        # Assicura campi obbligatori minimi
        codice_amministrativo = kwargs.get(
            "codice_amministrativo", SoggettiUtils.genera_codice_amministrativo()
        )

        sezione = kwargs.get("sezione", random.choice(string.ascii_uppercase))

        identificativo_soggetto = kwargs.get(
            "identificativo_soggetto", str(random.randint(1000, 999999999)).zfill(15)
        )

        # Genera una persona fisica con i dati correlati
        sesso = kwargs.get("sesso", random.choice([item for item in SessoEnum]))
        cognome = kwargs.get("cognome", fake.last_name())
        nome = kwargs.get(
            "nome",
            fake.first_name_male()
            if sesso == SessoEnum.MASCHIO
            else fake.first_name_female(),
        )
        data_di_nascita = kwargs.get(
            "data_di_nascita", SoggettiUtils.genera_formato_data()
        )
        luogo_di_nascita = kwargs.get(
            "luogo_di_nascita", SoggettiUtils.genera_luogo_nascita()
        )
        codice_fiscale = kwargs.get(
            "codice_fiscale", SoggettiUtils.genera_codice_fiscale_persona()
        )
        indicazioni_supplementari = kwargs.get(
            "indicazioni_supplementari",
            fake.text(max_nb_chars=16) if random.random() > 0.7 else None,
        )

        # Prepara il dizionario con i campi richiesti
        data = {
            "codice_amministrativo": codice_amministrativo,
            "sezione": sezione,
            "identificativo_soggetto": identificativo_soggetto,
            "tipo_soggetto": TipoSoggettoEnum.PERSONA_FISICA,
            "cognome": cognome,
            "nome": nome,
            "sesso": sesso,
            "data_di_nascita": data_di_nascita,
            "luogo_di_nascita": luogo_di_nascita,
            "codice_fiscale": codice_fiscale,
        }

        # Aggiungi campi opzionali se presenti
        if indicazioni_supplementari:
            data["indicazioni_supplementari"] = indicazioni_supplementari

        # Costruisci e valida l'oggetto
        return SoggettiRecordPrivatePerson(**data)


class SoggettiRecordGiuridicPersonFactory(ModelFactory[SoggettiRecordGiuridicPerson]):
    """Factory per generare oggetti SoggettiRecordGiuridicPerson."""

    __model__ = SoggettiRecordGiuridicPerson

    @classmethod
    def build(cls, **kwargs) -> SoggettiRecordGiuridicPerson:
        """
        Genera un oggetto SoggettiRecordGiuridicPerson con validazione rigorosa.

        Args:
            **kwargs: Parametri opzionali per personalizzare la generazione

        Returns:
            SoggettiRecordGiuridicPerson: Un'istanza validata del record
        """
        # Assicura campi obbligatori minimi
        codice_amministrativo = kwargs.get(
            "codice_amministrativo", SoggettiUtils.genera_codice_amministrativo()
        )

        sezione = kwargs.get("sezione", random.choice(string.ascii_uppercase))

        identificativo_soggetto = kwargs.get(
            "identificativo_soggetto", str(random.randint(1000, 999999999)).zfill(15)
        )

        # Genera una persona giuridica con i dati correlati
        denominazione = kwargs.get("denominazione", fake.company())
        sede = kwargs.get("sede", SoggettiUtils.genera_codice_amministrativo())
        codice_fiscale = kwargs.get(
            "codice_fiscale", SoggettiUtils.genera_codice_fiscale_azienda()
        )

        # Prepara il dizionario con i campi richiesti
        data = {
            "codice_amministrativo": codice_amministrativo,
            "sezione": sezione,
            "identificativo_soggetto": identificativo_soggetto,
            "tipo_soggetto": TipoSoggettoEnum.PERSONA_GIURIDICA,
            "denominazione": denominazione,
            "sede": sede,
            "codice_fiscale": codice_fiscale,
        }

        # Costruisci e valida l'oggetto
        return SoggettiRecordGiuridicPerson(**data)


class SoggettoFactory(ModelFactory[Soggetto]):
    """Factory per generare oggetti Soggetto."""

    __model__ = Soggetto

    @classmethod
    def build(cls, **kwargs) -> Soggetto:
        """Genera un soggetto completo."""
        # Genera i dati comuni
        codice_amministrativo = kwargs.get(
            "codice_amministrativo", SoggettiUtils.genera_codice_amministrativo()
        )
        sezione = kwargs.get("sezione", random.choice(string.ascii_uppercase))
        identificativo_soggetto = kwargs.get(
            "identificativo_soggetto", str(random.randint(1000, 999999999))
        )

        # Decidi casualmente se creare una persona fisica o giuridica
        tipo_soggetto = kwargs.get("tipo_soggetto", random.choice(["P", "G"]))

        # Genera il record appropriato in base al tipo di soggetto
        if tipo_soggetto == "P":
            record = kwargs.get(
                "record",
                SoggettiRecordPrivatePersonFactory.build(
                    codice_amministrativo=codice_amministrativo,
                    sezione=sezione,
                    identificativo_soggetto=identificativo_soggetto,
                ),
            )
        else:  # tipo_soggetto == "G"
            record = kwargs.get(
                "record",
                SoggettiRecordGiuridicPersonFactory.build(
                    codice_amministrativo=codice_amministrativo,
                    sezione=sezione,
                    identificativo_soggetto=identificativo_soggetto,
                ),
            )

        # Crea e restituisce il soggetto
        return Soggetto(
            codice_amministrativo=codice_amministrativo,
            sezione=sezione,
            identificativo_soggetto=identificativo_soggetto,
            tipo_soggetto=tipo_soggetto,
            record=record,
        )


class SoggettiTestGenerator:
    """Classe per generare dati di test per i file SOG."""

    @staticmethod
    def genera_file_soggetti(num_soggetti: int = 5) -> List[Any]:
        """
        Genera un file soggetti completo.

        Args:
            num_soggetti: Numero di soggetti da generare

        Returns:
            List: Lista di oggetti record
        """
        all_records = []

        for _ in range(num_soggetti):
            soggetto = SoggettoFactory.build()
            all_records.append(soggetto.record)

        return all_records

    @staticmethod
    def genera_file_content(records: List[Any]) -> str:
        """
        Converte i record in contenuto del file SOG.

        Args:
            records: Lista di oggetti record

        Returns:
            str: Contenuto del file SOG
        """
        lines = []

        for record in records:
            line = SoggettiTestGenerator._record_to_line(record)
            lines.append(line)

        return "\n".join(lines)

    @staticmethod
    def _record_to_line(
        record: Union[SoggettiRecordPrivatePerson, SoggettiRecordGiuridicPerson],
    ) -> str:
        """
        Converte un record in una linea del file SOG.

        Args:
            record: L'oggetto record da convertire

        Returns:
            str: La linea del file SOG
        """
        # Parte campi comuni a tutti
        header = f"{record.codice_amministrativo}|{record.sezione}|{record.identificativo_soggetto}|{record.tipo_soggetto}"

        # Inizia la parte dati
        data = ""

        # Aggiungi campi specifici in base al tipo di soggetto
        try:
            if record.tipo_soggetto == "P":
                # Formatta i campi per una persona fisica
                data_parts = [
                    record.cognome,
                    record.nome,
                    record.sesso,
                    record.data_di_nascita,
                    record.luogo_di_nascita,
                    record.codice_fiscale,
                    record.indicazioni_supplementari or "",
                ]
                data += "|".join(data_parts)

            elif record.tipo_soggetto == "G":
                # Formatta i campi per una persona giuridica
                data_parts = [
                    record.denominazione,
                    record.sede,
                    record.codice_fiscale,
                ]
                data += "|".join(data_parts)

            return f"{header}|{data}"
        except Exception as e:
            print(f"Errore nella conversione del record a linea: {e}")
            raise
