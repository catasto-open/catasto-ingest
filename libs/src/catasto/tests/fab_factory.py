import random
import string
from datetime import datetime, timedelta
from typing import Any, List

from catasto.schemas.building import (
    FabbricatiImmobile,
    FabbricatiRecord1,
    FabbricatiRecord2,
    FabbricatiRecord3,
    FabbricatiRecord4,
    FabbricatiRecord5,
    Identificativo,
    Indirizzo,
    Riserva,
    UtilitaComune,
)
from faker import Faker
from polyfactory.factories.pydantic_factory import ModelFactory

# Inizializzazione di Faker con impostazione locale italiana
fake = Faker(["it_IT"])
Faker.seed(42)  # Per riprodurre gli stessi dati casuali


class FabbricatiUtils:
    """Utility per la generazione di dati catastali specifici."""

    @staticmethod
    def genera_formato_data():
        """Genera una data casuale nel formato GGMMAAAA."""
        return fake.date_between(start_date="-31y", end_date="-1y").strftime("%d%m%Y")

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
    def genera_categoria():
        """Genera una categoria catastale valida."""
        prefix = random.choice(["A", "B", "C"])
        num = str(random.randint(1, 10)).zfill(2)
        return f"{prefix}{num}"

    @staticmethod
    def genera_consistenza(categoria: str):
        """Genera una consistenza coerente con la categoria."""
        if categoria.startswith("A"):
            # Vani (ultimo carattere 0 o 5)
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
    def genera_rendita_euro():
        """
        Genera una rendita in euro nel formato richiesto.

        Assicura che la stringa abbia esattamente 18 caratteri:
        - Parte intera: massimo 14 cifre, troncata se necessario
        - Parte decimale: sempre 3 cifre

        Returns:
            str: Rendita in euro nel formato corretto (15 cifre interi + .+ 3 decimali)
        """
        # Genera la parte intera (massimo 14 cifre)
        parte_intera = str(random.randint(0, 999999999999999)).zfill(14)[:14]

        # Genera la parte decimale (3 cifre)
        parte_decimale = str(random.randint(0, 999)).zfill(3)

        # Combina le parti
        return f"{parte_intera},{parte_decimale}"

    @staticmethod
    def genera_numero(edificialita=None):
        """Genera un numero particella coerente con l'edificialità."""
        if edificialita == "E":
            return f".{str(random.randint(1, 9999)).zfill(4)}"
        return str(random.randint(1, 99999)).zfill(5)


class IdentificativoFactory(ModelFactory[Identificativo]):
    """Factory per generare oggetti Identificativo."""

    __model__ = Identificativo

    @classmethod
    def build(cls, **kwargs) -> Identificativo:
        edificialita = kwargs.get("edificialita", random.choice(["E", " "]))

        sezione_urbana = kwargs.get(
            "sezione_urbana",
            fake.bothify(text="???", letters="ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
        )
        foglio = kwargs.get("foglio", str(random.randint(1, 9999)).zfill(4))
        denominatore = kwargs.get("denominatore", str(random.randint(0, 9999)).zfill(4))
        subalterno = kwargs.get("subalterno", str(random.randint(1, 9999)).zfill(4))

        # Genera numero in base all'edificialità
        numero = kwargs.get("numero")
        if not numero:
            if edificialita == "E":
                numero = f".{str(random.randint(1, 9999)).zfill(4)}"
            else:
                numero = str(random.randint(1, 99999)).zfill(5)

        return Identificativo(
            sezione_urbana=sezione_urbana,
            foglio=foglio,
            numero=numero,
            denominatore=denominatore,
            subalterno=subalterno,
            edificialita=edificialita,
        )


class IndirizzoFactory(ModelFactory[Indirizzo]):
    """Factory per generare oggetti Indirizzo."""

    __model__ = Indirizzo

    @classmethod
    def build(cls, **kwargs) -> Indirizzo:
        return Indirizzo(
            toponimo=kwargs.get("toponimo", str(random.randint(1, 999)).zfill(3)),
            indirizzo=kwargs.get("indirizzo", fake.street_name()[:50]),
            civico1=kwargs.get("civico1", str(random.randint(1, 999999)).zfill(6)),
            civico2=kwargs.get(
                "civico2",
                str(random.randint(1, 999999)).zfill(6)
                if random.random() > 0.7
                else None,
            ),
            civico3=kwargs.get(
                "civico3",
                str(random.randint(1, 999999)).zfill(6)
                if random.random() > 0.9
                else None,
            ),
            codice_strada=kwargs.get(
                "codice_strada", str(random.randint(1, 99999)).zfill(5)
            ),
        )


class UtilitaComuneFactory(ModelFactory[UtilitaComune]):
    """Factory per generare oggetti UtilitaComune."""

    __model__ = UtilitaComune

    @classmethod
    def build(cls, **kwargs) -> UtilitaComune:
        return UtilitaComune(
            sezione_urbana=kwargs.get(
                "sezione_urbana",
                fake.bothify(text="???", letters="ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
            ),
            foglio=kwargs.get("foglio", str(random.randint(1, 9999)).zfill(4)),
            numero=kwargs.get("numero", str(random.randint(1, 99999)).zfill(5)),
            denominatore=kwargs.get(
                "denominatore", str(random.randint(0, 9999)).zfill(4)
            ),
            subalterno=kwargs.get("subalterno", str(random.randint(1, 9999)).zfill(4)),
        )


class RiservaFactory(ModelFactory[Riserva]):
    """Factory per generare oggetti Riserva."""

    __model__ = Riserva

    @classmethod
    def build(cls, **kwargs) -> Riserva:
        return Riserva(
            codice_riserva=kwargs.get(
                "codice_riserva", random.choice(["A", "B", "C", "D", "E"])
            ),
            partita_iscrizione_riserva=kwargs.get(
                "partita_iscrizione_riserva", str(random.randint(1, 9999999)).zfill(7)
            ),
        )


class FabbricatiRecord1Factory(ModelFactory[FabbricatiRecord1]):
    """Factory per generare oggetti FabbricatiRecord1."""

    __model__ = FabbricatiRecord1

    @classmethod
    def build(cls, **kwargs) -> FabbricatiRecord1:
        """
        Genera un oggetto FabbricatiRecord1 con validazione rigorosa.

        Args:
            **kwargs: Parametri opzionali per personalizzare la generazione

        Returns:
            FabbricatiRecord1: Un'istanza validata del record
        """
        # Assicura campi obbligatori minimi
        codice_amministrativo = kwargs.get(
            "codice_amministrativo", FabbricatiUtils.genera_codice_amministrativo()
        )

        sezione = kwargs.get("sezione", random.choice(string.ascii_uppercase))

        identificativo_immobile = kwargs.get(
            "identificativo_immobile", str(random.randint(1000, 999999999)).zfill(15)
        )

        progressivo = kwargs.get("progressivo", str(random.randint(1, 999)).zfill(3))

        # Genera una categoria valida (campo obbligatorio)
        categoria = kwargs.get("categoria", FabbricatiUtils.genera_categoria())

        # Genera consistenza coerente con la categoria (campo obbligatorio)
        consistenza = kwargs.get(
            "consistenza", FabbricatiUtils.genera_consistenza(categoria)
        )

        # Genera classe (campo obbligatorio)
        classe = kwargs.get("classe", str(random.randint(1, 10)).zfill(2))

        # Genera zona (campo obbligatorio)
        zona = kwargs.get("zona", str(random.randint(1, 999)).zfill(3))

        # Genera date di efficacia e registrazione (campi obbligatori)
        data_efficacia_iniziale = kwargs.get(
            "data_efficacia_iniziale", FabbricatiUtils.genera_formato_data()
        )

        data_registrazione_atti_iniziale = kwargs.get(
            "data_registrazione_atti_iniziale",
            FabbricatiUtils.genera_formato_data(),
        )

        # Genera rendita euro (campo obbligatorio)
        rendita_euro = kwargs.get("rendita_euro", FabbricatiUtils.genera_rendita_euro())

        # Genera tipo_nota_iniziale (campo obbligatorio)
        tipo_nota_iniziale = kwargs.get(
            "tipo_nota_iniziale", random.choice(["V", "I", "A"])
        )

        # Genera numero_nota_iniziale (campo obbligatorio)
        numero_nota_iniziale = kwargs.get(
            "numero_nota_iniziale", str(random.randint(1, 999999)).zfill(6)
        )

        # Genera progressivo_nota_iniziale (campo obbligatorio)
        progressivo_nota_iniziale = kwargs.get(
            "progressivo_nota_iniziale", str(random.randint(1, 999)).zfill(3)
        )

        # Genera anno_nota_iniziale (campo obbligatorio)
        anno_nota_iniziale = kwargs.get(
            "anno_nota_iniziale", str(random.randint(2000, 2099))
        )

        # Prepara il dizionario con i campi minimi richiesti
        data = {
            "codice_amministrativo": codice_amministrativo,
            "sezione": sezione,
            "identificativo_immobile": identificativo_immobile,
            "tipo_immobile": "F",
            "progressivo": progressivo,
            "tipo_record": "1",
            "zona": zona,
            "categoria": categoria,
            "classe": classe,
            "consistenza": consistenza,
            "rendita_euro": rendita_euro,
            "data_efficacia_iniziale": data_efficacia_iniziale,
            "data_registrazione_atti_iniziale": data_registrazione_atti_iniziale,
            "tipo_nota_iniziale": tipo_nota_iniziale,
            "numero_nota_iniziale": numero_nota_iniziale,
            "progressivo_nota_iniziale": progressivo_nota_iniziale,
            "anno_nota_iniziale": anno_nota_iniziale,
        }

        # Aggiungi campi opzionali
        opzionali = {
            "superficie": kwargs.get(
                "superficie", str(random.randint(1, 99999)).zfill(5)
            ),
            "rendita_lire": kwargs.get(
                "rendita_lire", str(random.randint(1, 999999999999999)).zfill(15)
            ),
            "lotto": kwargs.get("lotto", str(random.randint(1, 99)).zfill(2)),
            "edificio": kwargs.get("edificio", str(random.randint(1, 99)).zfill(2)),
            "scala": kwargs.get("scala", str(random.randint(1, 99)).zfill(2)),
            "interno1": kwargs.get("interno1", str(random.randint(1, 999)).zfill(3)),
            "interno2": kwargs.get("interno2", str(random.randint(1, 999)).zfill(3)),
            "piano1": kwargs.get("piano1", str(random.randint(1, 9999)).zfill(4)),
            "piano2": kwargs.get("piano2", str(random.randint(1, 9999)).zfill(4)),
            "piano3": kwargs.get("piano3", str(random.randint(1, 9999)).zfill(4)),
            "piano4": kwargs.get("piano4", str(random.randint(1, 9999)).zfill(4)),
            "flag_classamento": kwargs.get(
                "flag_classamento", random.choice(["1", "2", "3", "4", "5", " "])
            ),
        }

        # Aggiungi date finali se necessario
        # if random.random() > 0.7:
        if data.get("data_efficacia_iniziale") and data.get(
            "data_registrazione_atti_iniziale"
        ):
            finale_data = {
                "data_efficacia_finale": FabbricatiUtils.genera_data_successiva(
                    data_efficacia_iniziale, 1, 30
                ),
                "data_registrazione_atti_finale": FabbricatiUtils.genera_data_successiva(
                    data_registrazione_atti_iniziale, 1, 30
                ),
                "tipo_nota_finale": random.choice(["V", "I", "A"]),
                "numero_nota_finale": str(random.randint(1, 999999)).zfill(6),
                "progressivo_nota_finale": str(random.randint(1, 999)).zfill(3),
                "anno_nota_finale": str(random.randint(1990, 2023)),
            }
            data.update(finale_data)

        # Aggiungi campi opzionali
        data.update({k: v for k, v in opzionali.items() if v is not None})

        # Aggiungi altri campi opzionali specifici
        extra_opzionali = {
            "partita": kwargs.get("partita", str(random.randint(1, 9999999)).zfill(7)),
            "annotazione": kwargs.get("annotazione", fake.sentence(nb_words=10)[:200]),
            "identificativo_mutazione_iniziale": kwargs.get(
                "identificativo_mutazione_iniziale",
                str(random.randint(1, 999999999)).zfill(9),
            ),
            "identificativo_mutazione_finale": kwargs.get(
                "identificativo_mutazione_finale",
                str(random.randint(1, 999999999)).zfill(9)
                if "data_efficacia_finale" in data
                else None,
            ),
            "protocollo_notifica": kwargs.get(
                "protocollo_notifica",
                str(random.randint(1, 999999999999999999)).zfill(18),
            ),
            "data_notifica": kwargs.get(
                "data_notifica", FabbricatiUtils.genera_formato_data()
            ),
            "codice_causale_atto_generante": kwargs.get(
                "codice_causale_atto_generante", str(random.randint(1, 999)).zfill(3)
            ),
            "descrizione_atto_generante": kwargs.get(
                "descrizione_atto_generante", fake.sentence(nb_words=5)[:100]
            ),
            "codice_causale_atto_conclusivo": kwargs.get(
                "codice_causale_atto_conclusivo",
                str(random.randint(1, 999)).zfill(3)
                if "data_efficacia_finale" in data
                else None,
            ),
            "descrizione_atto_conclusivo": kwargs.get(
                "descrizione_atto_conclusivo",
                fake.sentence(nb_words=5)[:100]
                if "data_efficacia_finale" in data
                else None,
            ),
        }

        # Aggiungi extra opzionali, rimuovendo i None
        data.update({k: v for k, v in extra_opzionali.items() if v is not None})

        # Costruisci e valida l'oggetto
        print(data)
        return FabbricatiRecord1(**data)


class FabbricatiRecord2Factory(ModelFactory[FabbricatiRecord2]):
    """Factory per generare oggetti FabbricatiRecord2."""

    __model__ = FabbricatiRecord2

    @classmethod
    def build(cls, **kwargs) -> FabbricatiRecord2:
        # Dati di base
        codice_amministrativo = kwargs.get(
            "codice_amministrativo", FabbricatiUtils.genera_codice_amministrativo()
        )
        sezione = kwargs.get("sezione", random.choice(string.ascii_uppercase))
        identificativo_immobile = kwargs.get(
            "identificativo_immobile", str(random.randint(1000, 999999999))
        )
        progressivo = kwargs.get("progressivo", str(random.randint(1, 999)).zfill(3))

        # Genera identificativi
        num_identificativi = kwargs.get("num_identificativi", random.randint(1, 3))
        identificativi = kwargs.get(
            "identificativi",
            [IdentificativoFactory.build() for _ in range(min(num_identificativi, 10))],
        )

        return FabbricatiRecord2(
            codice_amministrativo=codice_amministrativo,
            sezione=sezione,
            identificativo_immobile=identificativo_immobile,
            tipo_immobile="F",
            progressivo=progressivo,
            tipo_record="2",
            identificativi=identificativi,
        )


class FabbricatiRecord3Factory(ModelFactory[FabbricatiRecord3]):
    """Factory per generare oggetti FabbricatiRecord3."""

    __model__ = FabbricatiRecord3

    @classmethod
    def build(cls, **kwargs) -> FabbricatiRecord3:
        # Dati di base
        codice_amministrativo = kwargs.get(
            "codice_amministrativo", FabbricatiUtils.genera_codice_amministrativo()
        )
        sezione = kwargs.get("sezione", random.choice(string.ascii_uppercase))
        identificativo_immobile = kwargs.get(
            "identificativo_immobile", str(random.randint(1000, 999999999))
        )
        progressivo = kwargs.get("progressivo", str(random.randint(1, 999)).zfill(3))

        # Genera indirizzi
        num_indirizzi = kwargs.get("num_indirizzi", random.randint(1, 2))
        indirizzi = kwargs.get(
            "indirizzi",
            [IndirizzoFactory.build() for _ in range(min(num_indirizzi, 4))],
        )

        return FabbricatiRecord3(
            codice_amministrativo=codice_amministrativo,
            sezione=sezione,
            identificativo_immobile=identificativo_immobile,
            tipo_immobile="F",
            progressivo=progressivo,
            tipo_record="3",
            indirizzi=indirizzi,
        )


class FabbricatiRecord4Factory(ModelFactory[FabbricatiRecord4]):
    """Factory per generare oggetti FabbricatiRecord4."""

    __model__ = FabbricatiRecord4

    @classmethod
    def build(cls, **kwargs) -> FabbricatiRecord4:
        # Dati di base
        codice_amministrativo = kwargs.get(
            "codice_amministrativo", FabbricatiUtils.genera_codice_amministrativo()
        )
        sezione = kwargs.get("sezione", random.choice(string.ascii_uppercase))
        identificativo_immobile = kwargs.get(
            "identificativo_immobile", str(random.randint(1000, 999999999))
        )
        progressivo = kwargs.get("progressivo", str(random.randint(1, 999)).zfill(3))

        # Genera utilità comuni
        num_utilita = kwargs.get("num_utilita", random.randint(1, 2))
        utilita_comuni = kwargs.get(
            "utilita_comuni",
            [UtilitaComuneFactory.build() for _ in range(min(num_utilita, 10))],
        )

        return FabbricatiRecord4(
            codice_amministrativo=codice_amministrativo,
            sezione=sezione,
            identificativo_immobile=identificativo_immobile,
            tipo_immobile="F",
            progressivo=progressivo,
            tipo_record="4",
            utilita_comuni=utilita_comuni,
        )


class FabbricatiRecord5Factory(ModelFactory[FabbricatiRecord5]):
    """Factory per generare oggetti FabbricatiRecord5."""

    __model__ = FabbricatiRecord5

    @classmethod
    def build(cls, **kwargs) -> FabbricatiRecord5:
        # Dati di base
        codice_amministrativo = kwargs.get(
            "codice_amministrativo", FabbricatiUtils.genera_codice_amministrativo()
        )
        sezione = kwargs.get("sezione", random.choice(string.ascii_uppercase))
        identificativo_immobile = kwargs.get(
            "identificativo_immobile", str(random.randint(1000, 999999999))
        )
        progressivo = kwargs.get("progressivo", str(random.randint(1, 999)).zfill(3))

        # Genera riserve
        num_riserve = kwargs.get("num_riserve", random.randint(1, 2))
        riserve = kwargs.get(
            "riserve", [RiservaFactory.build() for _ in range(min(num_riserve, 10))]
        )

        return FabbricatiRecord5(
            codice_amministrativo=codice_amministrativo,
            sezione=sezione,
            identificativo_immobile=identificativo_immobile,
            tipo_immobile="F",
            progressivo=progressivo,
            tipo_record="5",
            riserve=riserve,
        )


class FabbricatiImmobileFactory(ModelFactory[FabbricatiImmobile]):
    """Factory per generare oggetti FabbricatiImmobile."""

    __model__ = FabbricatiImmobile

    @classmethod
    def build(cls, **kwargs) -> FabbricatiImmobile:
        """Genera un immobile completo con tutti i record necessari."""
        # Genera i dati comuni
        codice_amministrativo = kwargs.get(
            "codice_amministrativo", FabbricatiUtils.genera_codice_amministrativo()
        )
        sezione = kwargs.get("sezione", random.choice(string.ascii_uppercase))
        identificativo_immobile = kwargs.get(
            "identificativo_immobile", str(random.randint(1000, 999999999))
        )
        progressivo = kwargs.get("progressivo", str(random.randint(1, 999)).zfill(3))

        # Genera record1 (obbligatorio)
        record1 = kwargs.get(
            "record1",
            FabbricatiRecord1Factory.build(
                codice_amministrativo=codice_amministrativo,
                sezione=sezione,
                identificativo_immobile=identificativo_immobile,
                progressivo=progressivo,
            ),
        )

        # Genera record2 (obbligatorio)
        record2 = kwargs.get(
            "record2",
            FabbricatiRecord2Factory.build(
                codice_amministrativo=codice_amministrativo,
                sezione=sezione,
                identificativo_immobile=identificativo_immobile,
                progressivo=progressivo,
            ),
        )

        # Record opzionali
        record3 = kwargs.get("record3")
        if (
            record3 is None and random.random() > 0.2
        ):  # 80% di probabilità di avere record3
            record3 = FabbricatiRecord3Factory.build(
                codice_amministrativo=codice_amministrativo,
                sezione=sezione,
                identificativo_immobile=identificativo_immobile,
                progressivo=progressivo,
            )

        record4 = kwargs.get("record4")
        if (
            record4 is None and random.random() > 0.7
        ):  # 30% di probabilità di avere record4
            record4 = FabbricatiRecord4Factory.build(
                codice_amministrativo=codice_amministrativo,
                sezione=sezione,
                identificativo_immobile=identificativo_immobile,
                progressivo=progressivo,
            )

        record5 = kwargs.get("record5")
        if (
            record5 is None and random.random() > 0.8
        ):  # 20% di probabilità di avere record5
            record5 = FabbricatiRecord5Factory.build(
                codice_amministrativo=codice_amministrativo,
                sezione=sezione,
                identificativo_immobile=identificativo_immobile,
                progressivo=progressivo,
            )

        # Crea e restituisce l'immobile
        return FabbricatiImmobile(
            codice_amministrativo=codice_amministrativo,
            sezione=sezione,
            identificativo_immobile=identificativo_immobile,
            tipo_immobile="F",
            progressivo=progressivo,
            record1=record1,
            record2=record2,
            record3=record3,
            record4=record4,
            record5=record5,
        )


class FabbricatiTestGenerator:
    """Classe per generare dati di test per i file FAB."""

    @staticmethod
    def genera_immobile_completo() -> List[Any]:
        """
        Genera un set completo di record per un immobile.

        Returns:
            List: Lista di oggetti record
        """
        immobile = FabbricatiImmobileFactory.build()

        # Raccogli tutti i record in una lista
        records = [immobile.record1, immobile.record2]
        if immobile.record3:
            records.append(immobile.record3)
        if immobile.record4:
            records.append(immobile.record4)
        if immobile.record5:
            records.append(immobile.record5)

        return records

    @staticmethod
    def genera_file_fabbricati(num_immobili: int = 5) -> List[Any]:
        """
        Genera un file fabbricati completo.

        Args:
            num_immobili: Numero di immobili da generare

        Returns:
            List: Lista di oggetti record
        """
        all_records = []

        for _ in range(num_immobili):
            records = FabbricatiTestGenerator.genera_immobile_completo()
            all_records.extend(records)

        return all_records

    @staticmethod
    def genera_file_content(records: List[Any]) -> str:
        """
        Converte i record in contenuto del file FAB.

        Args:
            records: Lista di oggetti record

        Returns:
            str: Contenuto del file FAB
        """
        lines = []

        for record in records:
            line = FabbricatiTestGenerator._record_to_line(record)
            lines.append(line)

        return "\n".join(lines)

    @staticmethod
    def _record_to_line(record: Any) -> str:
        """
        Converte un record in una linea del file FAB.

        Args:
            record: L'oggetto record da convertire

        Returns:
            str: La linea del file FAB
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
                    record.zona,
                    record.categoria,
                    record.classe,
                    record.consistenza,
                    record.superficie or "",
                    record.rendita_lire or "",
                    record.rendita_euro,
                    record.lotto or "",
                    record.edificio or "",
                    record.scala or "",
                    record.interno1 or "",
                    record.interno2 or "",
                    record.piano1 or "",
                    record.piano2 or "",
                    record.piano3 or "",
                    record.piano4 or "",
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
                    record.protocollo_notifica or "",
                    record.data_notifica or "",
                    record.codice_causale_atto_generante or "",
                    record.descrizione_atto_generante or "",
                    record.codice_causale_atto_conclusivo or "",
                    record.descrizione_atto_conclusivo or "",
                    record.flag_classamento or "",
                ]
                data += "|".join(data_parts)

            elif record.tipo_record == "2":
                # Formatta gli identificativi per il record di tipo 2
                identificativi_parts = []
                for identificativo in record.identificativi:
                    part = "|".join(
                        [
                            identificativo.sezione_urbana,
                            identificativo.foglio,
                            identificativo.numero,
                            identificativo.denominatore,
                            identificativo.subalterno,
                            identificativo.edificialita,
                        ]
                    )
                    identificativi_parts.append(part)

                data += "|".join(identificativi_parts)

            elif record.tipo_record == "3":
                # Formatta gli indirizzi per il record di tipo 3
                indirizzi_parts = []
                for indirizzo in record.indirizzi:
                    part = "|".join(
                        [
                            indirizzo.toponimo,
                            indirizzo.indirizzo,
                            indirizzo.civico1 or "",
                            indirizzo.civico2 or "",
                            indirizzo.civico3 or "",
                            indirizzo.codice_strada,
                        ]
                    )
                    indirizzi_parts.append(part)

                data += "|".join(indirizzi_parts)

            elif record.tipo_record == "4":
                # Formatta le utilità comuni per il record di tipo 4
                utilita_parts = []
                for utilita in record.utilita_comuni:
                    part = "|".join(
                        [
                            utilita.sezione_urbana,
                            utilita.foglio,
                            utilita.numero,
                            utilita.denominatore,
                            utilita.subalterno,
                        ]
                    )
                    utilita_parts.append(part)

                data += "|".join(utilita_parts)

            elif record.tipo_record == "5":
                # Formatta le riserve per il record di tipo 5
                riserve_parts = []
                for riserva in record.riserve:
                    part = "|".join(
                        [
                            riserva.codice_riserva,
                            riserva.partita_iscrizione_riserva,
                        ]
                    )
                    riserve_parts.append(part)

                data += "|".join(riserve_parts)

            return f"{header}|{data}"
        except Exception as e:
            print(e)
            raise
