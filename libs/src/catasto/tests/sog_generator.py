# Generatori di dati casuali per i campi specifici
import random
import string

from catasto.schemas.subject import (
    SessoEnum,
    SoggettiRecordGiuridicPerson,
    SoggettiRecordPrivatePerson,
    Soggetto,
    TipoSoggettoEnum,
)
from faker import Faker

# Inizializzazione di Faker con impostazione locale italiana
fake = Faker(["it_IT"])
Faker.seed(42)  # Per riprodurre gli stessi dati casuali


class SoggettiGenerator:
    """Generatore di dati casuali per i file soggetti."""

    @staticmethod
    def genera_codice_amministrativo():
        """Genera un codice amministrativo casuale."""
        return f"{random.choice(string.ascii_uppercase)}{random.randint(100, 999)}"

    @staticmethod
    def genera_sezione():
        """Genera una sezione casuale."""
        return random.choice(string.ascii_uppercase)

    @staticmethod
    def genera_identificativo_soggetto():
        """Genera un identificativo soggetto casuale."""
        # Genera un numero casuale tra 1000 e 999999999
        return str(random.randint(1000, 999999999))

    @staticmethod
    def genera_tipo_soggetto():
        """Genera un tipo soggetto casuale."""
        return random.choice(["P", "G"])

    @staticmethod
    def genera_cognome():
        """Genera un cognome casuale."""
        return fake.last_name()

    @staticmethod
    def genera_nome():
        """Genera un nome casuale."""
        return fake.first_name()

    @staticmethod
    def genera_sesso():
        """Genera un sesso casuale."""
        return random.choice([item.value for item in SessoEnum])

    @staticmethod
    def genera_data_di_nascita():
        """Genera una data di nascita casuale nel formato GGMMAAAA."""
        date = fake.date_between(start_date="-80y", end_date="-18y")
        if date.month > 12:
            # Nel caso improbabile che il mese sia > 12, lo correggiamo
            date = date.replace(month=date.month % 12 or 12)
        return date.strftime("%d%m%Y")

    @staticmethod
    def genera_luogo_di_nascita():
        """Genera un luogo di nascita casuale."""
        return f"{random.choice(string.ascii_uppercase)}{random.randint(100, 999)}"

    @staticmethod
    def genera_codice_fiscale_persona():
        """Genera un codice fiscale casuale per persona fisica."""
        return fake.ssn()  # In Italia, fake.ssn() genera un codice fiscale valido

    @staticmethod
    def genera_indicazioni_supplementari():
        """Genera indicazioni supplementari casuali."""
        return fake.text(max_nb_chars=16) if random.random() > 0.7 else None

    @staticmethod
    def genera_denominazione():
        """Genera una denominazione casuale per persona giuridica."""
        return fake.company()

    @staticmethod
    def genera_sede():
        """Genera una sede casuale."""
        return f"{random.choice(string.ascii_uppercase)}{random.randint(100, 999)}"

    @staticmethod
    def genera_codice_fiscale_azienda():
        """Genera un codice fiscale casuale per persona giuridica."""
        # Le partite IVA italiane sono di 11 cifre
        return "".join([str(random.randint(0, 9)) for _ in range(11)])

    @staticmethod
    def genera_record_persona_fisica():
        """Genera un record di tipo persona fisica casuale."""
        codice_amministrativo = SoggettiGenerator.genera_codice_amministrativo()
        sezione = SoggettiGenerator.genera_sezione()
        identificativo_soggetto = SoggettiGenerator.genera_identificativo_soggetto()
        sesso = SoggettiGenerator.genera_sesso()

        record = {
            "codice_amministrativo": codice_amministrativo,
            "sezione": sezione,
            "identificativo_soggetto": identificativo_soggetto,
            "tipo_soggetto": TipoSoggettoEnum.PERSONA_FISICA,
            "cognome": SoggettiGenerator.genera_cognome(),
            "nome": SoggettiGenerator.genera_nome(),
            "sesso": sesso,
            "data_di_nascita": SoggettiGenerator.genera_data_di_nascita(),
            "luogo_di_nascita": SoggettiGenerator.genera_luogo_di_nascita(),
            "codice_fiscale": SoggettiGenerator.genera_codice_fiscale_persona(),
        }

        # Campo opzionale
        indicazioni_supplementari = SoggettiGenerator.genera_indicazioni_supplementari()
        if indicazioni_supplementari:
            record["indicazioni_supplementari"] = indicazioni_supplementari

        return record, (
            codice_amministrativo,
            sezione,
            identificativo_soggetto,
            "P",
        )

    @staticmethod
    def genera_record_persona_giuridica():
        """Genera un record di tipo persona giuridica casuale."""
        codice_amministrativo = SoggettiGenerator.genera_codice_amministrativo()
        sezione = SoggettiGenerator.genera_sezione()
        identificativo_soggetto = SoggettiGenerator.genera_identificativo_soggetto()

        record = {
            "codice_amministrativo": codice_amministrativo,
            "sezione": sezione,
            "identificativo_soggetto": identificativo_soggetto,
            "tipo_soggetto": TipoSoggettoEnum.PERSONA_GIURIDICA,
            "denominazione": SoggettiGenerator.genera_denominazione(),
            "sede": SoggettiGenerator.genera_sede(),
            "codice_fiscale": SoggettiGenerator.genera_codice_fiscale_azienda(),
        }

        return record, (
            codice_amministrativo,
            sezione,
            identificativo_soggetto,
            "G",
        )

    @staticmethod
    def genera_soggetto():
        """Genera un soggetto casuale (persona fisica o giuridica)."""
        tipo_soggetto = SoggettiGenerator.genera_tipo_soggetto()

        if tipo_soggetto == "P":
            record_data, key = SoggettiGenerator.genera_record_persona_fisica()
            record = SoggettiRecordPrivatePerson(**record_data)
        else:
            record_data, key = SoggettiGenerator.genera_record_persona_giuridica()
            record = SoggettiRecordGiuridicPerson(**record_data)

        codice_amministrativo, sezione, identificativo_soggetto, tipo = key

        return Soggetto(
            codice_amministrativo=codice_amministrativo,
            sezione=sezione,
            identificativo_soggetto=identificativo_soggetto,
            tipo_soggetto=tipo,
            record=record,
        )

    @staticmethod
    def genera_file_soggetti(num_soggetti=5):
        """Genera un file soggetti completo."""
        all_soggetti = []

        for _ in range(num_soggetti):
            soggetto = SoggettiGenerator.genera_soggetto()
            all_soggetti.append(soggetto)

        return all_soggetti

    @staticmethod
    def genera_file_content(soggetti):
        """Genera il contenuto del file SOG da una lista di soggetti."""
        lines = []

        for soggetto in soggetti:
            line = SoggettiGenerator._record_to_line(soggetto.record)
            lines.append(line)

        return "\n".join(lines)

    @staticmethod
    def _record_to_line(record):
        """Converte un record in una linea del file SOG."""
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
