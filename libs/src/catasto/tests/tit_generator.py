# Generatori di dati casuali per i campi specifici
import random
import string

from catasto.schemas.entitlement import (
    TipoImmobileEnum,
    TipoRegimeEnum,
    TipoSoggettoEnum,
    Titolarita,
)
from faker import Faker

# Inizializzazione di Faker con impostazione locale italiana
fake = Faker(["it_IT"])
Faker.seed(42)  # Per riprodurre gli stessi dati casuali


class TitolaritaGenerator:
    """Generatore di dati casuali per i file titolarità."""

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
        return str(random.randint(1000, 999999999))

    @staticmethod
    def genera_tipo_soggetto():
        """Genera un tipo soggetto casuale."""
        return random.choice([item.value for item in TipoSoggettoEnum])

    @staticmethod
    def genera_identificativo_immobile():
        """Genera un identificativo immobile casuale."""
        return str(random.randint(1000, 999999999))

    @staticmethod
    def genera_tipo_immobile():
        """Genera un tipo immobile casuale."""
        return random.choice([item.value for item in TipoImmobileEnum])

    @staticmethod
    def genera_codice_diritto():
        """Genera un codice diritto casuale."""
        return str(random.randint(1, 100))

    @staticmethod
    def genera_titolo_non_codificato():
        """Genera un titolo non codificato casuale."""
        return fake.sentence(nb_words=3)[:100] if random.random() > 0.7 else ""

    @staticmethod
    def genera_quota_numeratore():
        """Genera una quota numeratore casuale."""
        return str(random.randint(1, 100))

    @staticmethod
    def genera_quota_denominatore():
        """Genera una quota denominatore casuale."""
        return str(random.randint(1, 100))

    @staticmethod
    def genera_regime():
        """Genera un regime casuale."""
        return random.choice([item.value for item in TipoRegimeEnum])

    @staticmethod
    def genera_soggetto_di_riferimento():
        """Genera un soggetto di riferimento casuale."""
        return TitolaritaGenerator.genera_identificativo_soggetto()

    @staticmethod
    def genera_data_formato_catasto():
        """Genera una data casuale nel formato GGMMAAAA."""
        # Genera una data tra il 1990 e il 2022
        date = fake.date_between(start_date="-32y", end_date="-1y")
        # Correzione per il mese
        if date.month > 12:
            date = date.replace(month=date.month % 12 or 12)
        return date.strftime("%d%m%Y")

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
        return str(random.randint(1, 999)).zfill(3)

    @staticmethod
    def genera_descrizione_atto():
        """Genera una descrizione atto casuale."""
        return fake.sentence(nb_words=5)[:100]

    @staticmethod
    def genera_record_titolarita():
        """Genera un record di titolarità casuale."""
        codice_amministrativo = TitolaritaGenerator.genera_codice_amministrativo()
        sezione = TitolaritaGenerator.genera_sezione()
        identificativo_soggetto = TitolaritaGenerator.genera_identificativo_soggetto()
        tipo_soggetto = TitolaritaGenerator.genera_tipo_soggetto()
        identificativo_immobile = TitolaritaGenerator.genera_identificativo_immobile()
        tipo_immobile = TitolaritaGenerator.genera_tipo_immobile()

        # Date di riferimento
        data_validita_iniziale = TitolaritaGenerator.genera_data_formato_catasto()
        data_registrazione_iniziale = TitolaritaGenerator.genera_data_formato_catasto()

        # Flag per generare dati finali (30% di probabilità)
        genera_dati_finali = random.random() > 0.7

        record = {
            "codice_amministrativo": codice_amministrativo,
            "sezione": sezione,
            "identificativo_soggetto": identificativo_soggetto,
            "tipo_soggetto": TipoSoggettoEnum(tipo_soggetto),
            "identificativo_immobile": identificativo_immobile,
            "tipo_immobile": TipoImmobileEnum(tipo_immobile),
            "codice_diritto": TitolaritaGenerator.genera_codice_diritto(),
            "titolo_non_codificato": TitolaritaGenerator.genera_titolo_non_codificato(),
            "quota_numeratore": TitolaritaGenerator.genera_quota_numeratore(),
            "quota_denominatore": TitolaritaGenerator.genera_quota_denominatore(),
            "regime": TipoRegimeEnum(TitolaritaGenerator.genera_regime()),
            "soggetto_di_riferimento": TitolaritaGenerator.genera_soggetto_di_riferimento(),
            "data_di_validita_iniziale": data_validita_iniziale,
            "tipo_nota_iniziale": TitolaritaGenerator.genera_tipo_nota(),
            "numero_nota_iniziale": TitolaritaGenerator.genera_numero_nota(),
            "progressivo_nota_iniziale": TitolaritaGenerator.genera_progressivo_nota(),
            "anno_nota_iniziale": TitolaritaGenerator.genera_anno_nota(),
            "data_registrazione_atti_iniziale": data_registrazione_iniziale,
            "partita": TitolaritaGenerator.genera_partita(),
            "identificativo_mutazione_iniziale": TitolaritaGenerator.genera_identificativo_mutazione(),
            "identificativo_titolarita": TitolaritaGenerator.genera_identificativo_titolarita(),
            "codice_causale_atto_generante": TitolaritaGenerator.genera_codice_causale(),
            "descrizione_atto_generante": TitolaritaGenerator.genera_descrizione_atto(),
        }

        # Aggiungi dati finali se necessario
        if genera_dati_finali:
            record.update(
                {
                    "data_di_validita_finale": TitolaritaGenerator.genera_data_formato_catasto(),
                    "tipo_nota_finale": TitolaritaGenerator.genera_tipo_nota(),
                    "numero_nota_finale": TitolaritaGenerator.genera_numero_nota(),
                    "progressivo_nota_finale": TitolaritaGenerator.genera_progressivo_nota(),
                    "anno_nota_finale": TitolaritaGenerator.genera_anno_nota(),
                    "data_registrazione_atti_finale": TitolaritaGenerator.genera_data_formato_catasto(),
                    "identificativo_mutazione_finale": TitolaritaGenerator.genera_identificativo_mutazione(),
                    "codice_causale_atto_conclusivo": TitolaritaGenerator.genera_codice_causale(),
                    "descrizione_atto_conclusivo": TitolaritaGenerator.genera_descrizione_atto(),
                }
            )

        return record, (
            codice_amministrativo,
            sezione,
            identificativo_soggetto,
            tipo_soggetto,
            identificativo_immobile,
            tipo_immobile,
        )

    @staticmethod
    def genera_titolarita():
        """Genera una titolarità completa."""
        record_data, key = TitolaritaGenerator.genera_record_titolarita()

        try:
            # Crea l'oggetto Titolarita
            titolarita = Titolarita(**record_data)
            return titolarita
        except Exception as e:
            print(f"Errore nella creazione della titolarità: {e}")
            raise

    @staticmethod
    def genera_file_titolarita(num_titolarita=5):
        """Genera un file titolarità completo."""
        all_titolarita = []

        for _ in range(num_titolarita):
            try:
                titolarita = TitolaritaGenerator.genera_titolarita()
                all_titolarita.append(titolarita)
            except Exception as e:
                print(f"Errore nella generazione della titolarità: {e}")
                # Continua con la prossima titolarità

        return all_titolarita

    @staticmethod
    def genera_file_content(titolarita_list):
        """Genera il contenuto del file TIT."""
        lines = []

        for titolarita in titolarita_list:
            line = TitolaritaGenerator._record_to_line(titolarita)
            lines.append(line)

        return "\n".join(lines)

    @staticmethod
    def _record_to_line(titolarita):
        """Converte un record in una linea del file TIT."""
        # Parte campi comuni a tutti
        header = f"{titolarita.codice_amministrativo}|{titolarita.sezione}|{titolarita.identificativo_soggetto}|{titolarita.tipo_soggetto}|{titolarita.identificativo_immobile}|{titolarita.tipo_immobile}"

        # Formatta i campi specifici di titolarità
        data_parts = [
            titolarita.codice_diritto,
            titolarita.titolo_non_codificato or "",
            titolarita.quota_numeratore,
            titolarita.quota_denominatore,
            titolarita.regime.value if titolarita.regime else "",
            titolarita.soggetto_di_riferimento,
            titolarita.data_di_validita_iniziale or "",
            titolarita.tipo_nota_iniziale,
            titolarita.numero_nota_iniziale,
            titolarita.progressivo_nota_iniziale,
            titolarita.anno_nota_iniziale,
            titolarita.data_registrazione_atti_iniziale or "",
            titolarita.partita or "",
            titolarita.data_di_validita_finale or "",
            titolarita.tipo_nota_finale or "",
            titolarita.numero_nota_finale or "",
            titolarita.progressivo_nota_finale or "",
            titolarita.anno_nota_finale or "",
            titolarita.data_registrazione_atti_finale or "",
            titolarita.identificativo_mutazione_iniziale or "",
            titolarita.identificativo_mutazione_finale or "",
            titolarita.identificativo_titolarita,
            titolarita.codice_causale_atto_generante or "",
            titolarita.descrizione_atto_generante or "",
            titolarita.codice_causale_atto_conclusivo or "",
            titolarita.descrizione_atto_conclusivo or "",
        ]

        data = "|".join(data_parts)

        return f"{header}|{data}"
