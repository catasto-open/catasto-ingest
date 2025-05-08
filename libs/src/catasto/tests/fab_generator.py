# Generatori di dati casuali per i campi specifici
import random
import string

from catasto.schemas.building import (
    FabbricatiRecord1,
    FabbricatiRecord2,
    FabbricatiRecord3,
    FabbricatiRecord4,
    FabbricatiRecord5,
)
from faker import Faker

# Inizializzazione di Faker con impostazione locale italiana
fake = Faker(["it_IT"])
Faker.seed(42)  # Per riprodurre gli stessi dati casuali


class FabbricatiGenerator:
    """Generatore di dati casuali per i file fabbricati."""

    @staticmethod
    def genera_codice_amministrativo():
        """Genera un codice amministrativo casuale."""
        return fake.bothify(text="????", letters=string.digits).upper()

    @staticmethod
    def genera_sezione():
        """Genera una sezione casuale."""
        return random.choice(string.ascii_uppercase)

    @staticmethod
    def genera_identificativo_immobile():
        """Genera un identificativo immobile casuale."""
        # Genera un numero casuale tra 1000 e 999999999
        return str(random.randint(1000, 999999999))

    @staticmethod
    def genera_progressivo():
        """Genera un progressivo casuale."""
        return str(random.randint(1, 999)).zfill(3)

    @staticmethod
    def genera_zona():
        """Genera una zona casuale."""
        return str(random.randint(1, 999)).zfill(3)

    @staticmethod
    def genera_categoria():
        """Genera una categoria catastale casuale."""
        prefix = random.choice(["A", "B", "C"])
        num = str(random.randint(1, 10)).zfill(2)
        return f"{prefix}{num}"

    @staticmethod
    def genera_classe():
        """Genera una classe catastale casuale."""
        return str(random.randint(1, 10)).zfill(2)

    @staticmethod
    def genera_consistenza(categoria):
        """Genera una consistenza casuale in base alla categoria."""
        if categoria.startswith("A"):
            # Vani (ultimo carattere 0 o 5)
            # Genera un numero che finisce per 0 o 5
            base = random.randint(1, 199)
            ultimo_digit = random.choice([0, 5])
            valore = base * 10 + ultimo_digit
            return str(valore).zfill(7)
        elif categoria.startswith("B"):
            # Metri cubi
            return str(random.randint(100, 9999999)).zfill(7)
        else:  # categoria.startswith('C')
            # Metri quadrati
            return str(random.randint(100, 9999999)).zfill(7)

    @staticmethod
    def genera_superficie():
        """Genera una superficie casuale."""
        return str(random.randint(1, 99999)).zfill(5)

    @staticmethod
    def genera_rendita_lire():
        """Genera una rendita in lire casuale."""
        return str(random.randint(1, 999999999999999)).zfill(15)

    def genera_rendita_euro():
        """Genera una rendita in euro casuale."""
        # Formato: intero.3 decimali
        # Assicurarsi che la lunghezza totale sia esattamente 18 caratteri (14 + punto + 3)
        intero = str(random.randint(1, 99999999999999)).zfill(
            14
        )  # Esattamente 14 cifre
        decimali = str(random.randint(0, 999)).zfill(3)  # Esattamente 3 cifre
        return f"{intero}.{decimali}"  # Totale: 14 + 1 + 3 = 18 caratteri

    @staticmethod
    def genera_data_formato_catasto():
        """Genera una data casuale nel formato GGMMAAAA."""
        # Genera una data tra il 1990 e il 2022
        return fake.date_between(start_date="-32y", end_date="-1y").strftime("%d%m%Y")

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
    def genera_flag_classamento():
        """Genera un flag classamento casuale."""
        return random.choice(["1", "2", "3", "4", "5", " "])

    @staticmethod
    def genera_sezione_urbana():
        """Genera una sezione urbana casuale."""
        return fake.bothify(text="???", letters="ABCDEFGHIJKLMNOPQRSTUVWXYZ")

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
    def genera_toponimo():
        """Genera un toponimo casuale."""
        return str(random.randint(1, 999)).zfill(3)

    @staticmethod
    def genera_indirizzo():
        """Genera un indirizzo casuale."""
        return fake.street_name()[:50]

    @staticmethod
    def genera_civico():
        """Genera un civico casuale."""
        return str(random.randint(1, 999999)).zfill(6)

    @staticmethod
    def genera_codice_strada():
        """Genera un codice strada casuale."""
        return str(random.randint(1, 99999)).zfill(5)

    @staticmethod
    def genera_codice_riserva():
        """Genera un codice riserva casuale."""
        return random.choice(["A", "B", "C", "D", "E"])

    @staticmethod
    def genera_record1():
        """Genera un record di tipo 1 casuale."""
        codice_amministrativo = FabbricatiGenerator.genera_codice_amministrativo()
        sezione = FabbricatiGenerator.genera_sezione()
        identificativo_immobile = FabbricatiGenerator.genera_identificativo_immobile()
        progressivo = FabbricatiGenerator.genera_progressivo()

        # Genera dati di classamento
        categoria = FabbricatiGenerator.genera_categoria()

        record = {
            "codice_amministrativo": codice_amministrativo,
            "sezione": sezione,
            "identificativo_immobile": identificativo_immobile,
            "tipo_immobile": "F",
            "progressivo": progressivo,
            "tipo_record": "1",
            "zona": FabbricatiGenerator.genera_zona(),
            "categoria": categoria,
            "classe": FabbricatiGenerator.genera_classe(),
            "consistenza": FabbricatiGenerator.genera_consistenza(categoria),
            "superficie": FabbricatiGenerator.genera_superficie(),
            "rendita_lire": FabbricatiGenerator.genera_rendita_lire(),
            "rendita_euro": FabbricatiGenerator.genera_rendita_euro(),
            "lotto": str(random.randint(1, 99)).zfill(2),
            "edificio": str(random.randint(1, 99)).zfill(2),
            "scala": str(random.randint(1, 99)).zfill(2),
            "interno1": str(random.randint(1, 999)).zfill(3),
            "interno2": str(random.randint(1, 999)).zfill(3),
            "piano1": str(random.randint(1, 9999)).zfill(4),
            "piano2": str(random.randint(1, 9999)).zfill(4),
            "piano3": str(random.randint(1, 9999)).zfill(4),
            "piano4": str(random.randint(1, 9999)).zfill(4),
            "data_efficacia_iniziale": FabbricatiGenerator.genera_data_formato_catasto(),
            "data_registrazione_atti_iniziale": FabbricatiGenerator.genera_data_formato_catasto(),
            "tipo_nota_iniziale": FabbricatiGenerator.genera_tipo_nota(),
            "numero_nota_iniziale": FabbricatiGenerator.genera_numero_nota(),
            "progressivo_nota_iniziale": FabbricatiGenerator.genera_progressivo_nota(),
            "anno_nota_iniziale": FabbricatiGenerator.genera_anno_nota(),
            "partita": FabbricatiGenerator.genera_partita(),
            "annotazione": FabbricatiGenerator.genera_annotazione(),
            "flag_classamento": FabbricatiGenerator.genera_flag_classamento(),
        }

        return record, (
            codice_amministrativo,
            sezione,
            identificativo_immobile,
            progressivo,
        )

    @staticmethod
    def genera_record2(
        codice_amministrativo,
        sezione,
        identificativo_immobile,
        progressivo,
        num_identificativi=1,
    ):
        """Genera un record di tipo 2 casuale."""
        identificativi = []

        for _ in range(num_identificativi):
            edificialita = FabbricatiGenerator.genera_edificialita()
            identificativi.append(
                {
                    "sezione_urbana": FabbricatiGenerator.genera_sezione_urbana(),
                    "foglio": FabbricatiGenerator.genera_foglio(),
                    "numero": FabbricatiGenerator.genera_numero(edificialita),
                    "denominatore": FabbricatiGenerator.genera_denominatore(),
                    "subalterno": FabbricatiGenerator.genera_subalterno(),
                    "edificialita": edificialita,
                }
            )

        record = {
            "codice_amministrativo": codice_amministrativo,
            "sezione": sezione,
            "identificativo_immobile": identificativo_immobile,
            "tipo_immobile": "F",
            "progressivo": progressivo,
            "tipo_record": "2",
            "identificativi": identificativi,
        }

        return record

    @staticmethod
    def genera_record3(
        codice_amministrativo,
        sezione,
        identificativo_immobile,
        progressivo,
        num_indirizzi=1,
    ):
        """Genera un record di tipo 3 casuale."""
        indirizzi = []

        for _ in range(num_indirizzi):
            indirizzi.append(
                {
                    "toponimo": FabbricatiGenerator.genera_toponimo(),
                    "indirizzo": FabbricatiGenerator.genera_indirizzo(),
                    "civico1": FabbricatiGenerator.genera_civico(),
                    "civico2": FabbricatiGenerator.genera_civico()
                    if random.random() > 0.7
                    else None,
                    "civico3": FabbricatiGenerator.genera_civico()
                    if random.random() > 0.9
                    else None,
                    "codice_strada": FabbricatiGenerator.genera_codice_strada(),
                }
            )

        record = {
            "codice_amministrativo": codice_amministrativo,
            "sezione": sezione,
            "identificativo_immobile": identificativo_immobile,
            "tipo_immobile": "F",
            "progressivo": progressivo,
            "tipo_record": "3",
            "indirizzi": indirizzi,
        }

        return record

    @staticmethod
    def genera_record4(
        codice_amministrativo,
        sezione,
        identificativo_immobile,
        progressivo,
        num_utilita=1,
    ):
        """Genera un record di tipo 4 casuale."""
        utilita_comuni = []

        for _ in range(num_utilita):
            utilita_comuni.append(
                {
                    "sezione_urbana": FabbricatiGenerator.genera_sezione_urbana(),
                    "foglio": FabbricatiGenerator.genera_foglio(),
                    "numero": FabbricatiGenerator.genera_numero(),
                    "denominatore": FabbricatiGenerator.genera_denominatore(),
                    "subalterno": FabbricatiGenerator.genera_subalterno(),
                }
            )

        record = {
            "codice_amministrativo": codice_amministrativo,
            "sezione": sezione,
            "identificativo_immobile": identificativo_immobile,
            "tipo_immobile": "F",
            "progressivo": progressivo,
            "tipo_record": "4",
            "utilita_comuni": utilita_comuni,
        }

        return record

    @staticmethod
    def genera_record5(
        codice_amministrativo,
        sezione,
        identificativo_immobile,
        progressivo,
        num_riserve=1,
    ):
        """Genera un record di tipo 5 casuale."""
        riserve = []

        for _ in range(num_riserve):
            riserve.append(
                {
                    "codice_riserva": FabbricatiGenerator.genera_codice_riserva(),
                    "partita_iscrizione_riserva": FabbricatiGenerator.genera_partita(),
                }
            )

        record = {
            "codice_amministrativo": codice_amministrativo,
            "sezione": sezione,
            "identificativo_immobile": identificativo_immobile,
            "tipo_immobile": "F",
            "progressivo": progressivo,
            "tipo_record": "5",
            "riserve": riserve,
        }

        return record

    @staticmethod
    def genera_immobile_completo():
        """Genera un set completo di record per un immobile."""
        record1, key = FabbricatiGenerator.genera_record1()
        codice_amministrativo, sezione, identificativo_immobile, progressivo = key

        record2 = FabbricatiGenerator.genera_record2(
            codice_amministrativo,
            sezione,
            identificativo_immobile,
            progressivo,
            num_identificativi=random.randint(1, 3),
        )

        # Record opzionali
        has_record3 = random.random() > 0.2
        has_record4 = random.random() > 0.7
        has_record5 = random.random() > 0.8

        records = [FabbricatiRecord1(**record1), FabbricatiRecord2(**record2)]

        if has_record3:
            record3 = FabbricatiGenerator.genera_record3(
                codice_amministrativo,
                sezione,
                identificativo_immobile,
                progressivo,
                num_indirizzi=random.randint(1, 2),
            )
            records.append(FabbricatiRecord3(**record3))

        if has_record4:
            record4 = FabbricatiGenerator.genera_record4(
                codice_amministrativo,
                sezione,
                identificativo_immobile,
                progressivo,
                num_utilita=random.randint(1, 2),
            )
            records.append(FabbricatiRecord4(**record4))

        if has_record5:
            record5 = FabbricatiGenerator.genera_record5(
                codice_amministrativo,
                sezione,
                identificativo_immobile,
                progressivo,
                num_riserve=random.randint(1, 2),
            )
            records.append(FabbricatiRecord5(**record5))

        return records

    @staticmethod
    def genera_file_fabbricati(num_immobili=5):
        """Genera un file fabbricati completo."""
        all_records = []

        for _ in range(num_immobili):
            records = FabbricatiGenerator.genera_immobile_completo()
            all_records.extend(records)

        return all
