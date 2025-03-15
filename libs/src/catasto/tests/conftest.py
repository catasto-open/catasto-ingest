import os
import pathlib
import tempfile

import pytest
from catasto.parser import FileParserService
from catasto.reader import LocalFileReaderService

from .fab_factory import FabbricatiRecord1Factory, FabbricatiTestGenerator
from .sog_factory import SoggettiTestGenerator
from .tit_factory import TitolaritaTestGenerator

directory = pathlib.Path("tests/data/")


@pytest.fixture
def local_sog_file():
    _file = directory / "textfile.SOG"
    return _file.absolute().__str__()


@pytest.fixture
def local_cxf_file():
    _file = directory / "H501D076700.CTF"
    return _file.absolute().__str__()


@pytest.fixture
def local_dir():
    _dir = directory
    return _dir.absolute().__str__()


@pytest.fixture
def local_file_reader(local_sog_file):
    return LocalFileReaderService(filepath=local_sog_file)


@pytest.fixture
def local_dir_reader(local_dir):
    return LocalFileReaderService(filepath=local_dir)


@pytest.fixture
def cxf_file_reader(local_cxf_file):
    return LocalFileReaderService(filepath=local_cxf_file)


@pytest.fixture
def cxf_parser(cxf_file_reader):
    return FileParserService(reader=cxf_file_reader)


@pytest.fixture
def cxf_content_generator():
    _file = directory / "H501D076700.CTF"
    content = _file.read_text()
    return iter(content.splitlines())


# --- Fixture per i file FAB ---


@pytest.fixture
def static_fab_record1_valid_line():
    """Ritorna un record FAB di tipo 1 valido da dati sintetici."""
    return "H501| |5810000|F|3|1|006|A02|06|6,5|141||1057,45||||1||T-1||||27012020|28012020|V|045227|001|2020|||||||||341274286||||VAR|QUESTA VIENE CONSIDERATA UNA SIMULAZIONE|||1|"  # noqa


@pytest.fixture
def static_fab_record1_invalid_line():
    """Ritorna un record FAB di tipo 1 non valido da dati sintetici."""
    return "HG01| |581A000|G|d|1|006|A02|06|6,5|141||1057,45||||1||T-1||||27012020|28012020|V|045227|001|2020|||||||||341274286||||VAR|QUESTA VIENE CONSIDERATA UNA SIMULAZIONE|||1|"  # noqa


@pytest.fixture
def static_fab_record2_valid_line():
    """Ritorna un record FAB di tipo 2 valido da dati sintetici."""
    return "H501| |351073|F|1|2||0142|00101||0004||"


@pytest.fixture
def static_fab_record2_invalid_line():
    """Ritorna un record FAB di tipo 2 valido da dati sintetici."""
    return "H501| |351073|F|1|2||0142|00101||0004|E|"  # Edificialità E vuole numero che comincia per .


@pytest.fixture
def static_fab_record3_valid_line():
    """Ritorna un record FAB di tipo 3 valido da dati sintetici."""
    return "H501| |4326|F|3|3|236|MARIO ROSSI|73|||603|"


@pytest.fixture
def static_fab_record3_invalid_line():
    """Ritorna un record FAB di tipo 3 valido da dati sintetici."""
    return "H501| |4326|F|3|3|2363|MARIO ROSSI|73|||603|"  # Toponimo deve essere massimo 3 caratteri


@pytest.fixture
def static_fab_record4_valid_line():
    """Ritorna un record FAB di tipo 4 valido da dati sintetici."""
    return "H501| |173704|F|2|4||0391|00329||||0391|00578|||"


@pytest.fixture
def static_fab_record4_invalid_line():
    """Ritorna un record FAB di tipo 4 valido da dati sintetici."""
    return "H501| |173704|F|2|4||0391|00329||||0391|00689||11111|"  # Subalterno deve essere massimo 4 caratteri


@pytest.fixture
def static_fab_record5_valid_line():
    """Ritorna un record FAB di tipo 5 valido da dati sintetici."""
    return "H501| |3675191|F|4|5|5||"


@pytest.fixture
def static_fab_record5_invalid_line():
    """Ritorna un record FAB di tipo 5 valido da dati sintetici."""
    return "H501| |3675191|F|4|5|5|1234567890|"  # Partita iscrizione riserva deve essere massimo 7 caratteri


# --- Fixture per i file SOG ---


@pytest.fixture
def static_sog_private_person_record_valid_line():
    """Ritorna un record SOG di tipo P valido da dati sintetici."""
    return "H501| |7125464|P|ROSSI|MARIO|1|01091973|H501|MRIRSS73P01LH501||"  # noqa


@pytest.fixture
def static_sog_private_person_record_invalid_line():
    """Ritorna un record SOG di tipo P non valido da dati sintetici."""
    return "H5011| |7125464|P|ROSSI|MARIO|3|01091973|H501|MRIRSS73P01LH501||"  # sesso deve essere 1 o 2, luogo di nascita massimo 4 caratteri


@pytest.fixture
def static_sog_giuridic_person_record_valid_line():
    """Ritorna un record SOG di tipo G valido da dati sintetici."""
    return "H501| |8363|G|COMUNE DI ROMA|H501|02437850856|"  # noqa


@pytest.fixture
def static_sog_giuridic_person_record_invalid_line():
    """Ritorna un record SOG di tipo G non valido da dati sintetici."""
    return "H501| |8363|G|COMUNE DI ROMA|H501|0243785085699|"  # partita IVA deve essere massimo 11 caratteri


# --- Fixture per i file TIT ---


@pytest.fixture
def static_tit_record_valid_line():
    """Ritorna un record TIT valido da dati sintetici."""
    return "H501| |54898|P|1437626|F|10||1|1| ||12112003|N|053614|001|2010|25082010||04062024|R|006985|001|2025|30012025|9167994|433188217|28099632|SEN|DIVISIONE|SEL|MARIO ROSSI|"  # noqa


@pytest.fixture
def static_tit_record_invalid_line():
    """Ritorna un record TIT non valido da dati sintetici."""
    return "H501| |54898|Y|1437626|X|10||1|1| ||12112003|N|053614|001|2010|25082010||04062024|R|006985|001|2025|30012025|9167994|433188217|28099632|SEN|DIVISIONE|SEL|MARIO ROSSI|"  # tipo_soggetto e tipo_immobile non validi


# --- Fixture per generazione di file ---


@pytest.fixture
def random_fab_record1():
    """Genera un record di tipo 1 casuale valido usando polyfactory."""
    return FabbricatiRecord1Factory.build()


@pytest.fixture
def random_immobile_completo():
    """Genera un set completo di record per un immobile usando polyfactory."""
    return FabbricatiTestGenerator.genera_immobile_completo()


@pytest.fixture
def temp_fab_file():
    """Crea un file FAB temporaneo con dati casuali generati da polyfactory."""
    with tempfile.NamedTemporaryFile(suffix=".FAB", delete=False) as f:
        records = FabbricatiTestGenerator.genera_file_fabbricati(num_immobili=3)
        content = FabbricatiTestGenerator.genera_file_content(records)
        f.write(content.encode("utf-8"))
        filepath = f.name

    # Restituisce il percorso del file
    yield filepath

    # Pulisce dopo il test
    os.unlink(filepath)


@pytest.fixture
def custom_fab_file():
    """Crea un file FAB con contenuto personalizzato usando polyfactory."""

    def _create_custom_file(num_immobili=3, con_errori=False):
        with tempfile.NamedTemporaryFile(suffix=".FAB", delete=False) as f:
            records = FabbricatiTestGenerator.genera_file_fabbricati(
                num_immobili=num_immobili
            )

            # Se richiesto, introduci errori
            if con_errori:
                # Modifica il contenuto direttamente nel file invece di modificare i record
                # Questo permette di mantenere la validazione Pydantic ma avere un file con errori
                content = FabbricatiTestGenerator.genera_file_content(records)
                # Sostituisce il tipo di immobile Fabbricato con un valore non valido
                content = content.replace("F", "M")
                f.write(content.encode("utf-8"))
            else:
                content = FabbricatiTestGenerator.genera_file_content(records)
                f.write(content.encode("utf-8"))

            filepath = f.name

        return filepath

    # Restituisce la funzione factory
    return _create_custom_file


@pytest.fixture
def random_soggetto_completo():
    """Genera un set completo di record per un soggetto usando polyfactory."""
    return SoggettiTestGenerator.genera_soggetto_completo()


@pytest.fixture
def temp_sog_file():
    """Crea un file SOG temporaneo con dati casuali generati da polyfactory."""
    with tempfile.NamedTemporaryFile(suffix=".SOG", delete=False) as f:
        records = SoggettiTestGenerator.genera_file_soggetti(num_soggetti=3)
        content = SoggettiTestGenerator.genera_file_content(records)
        f.write(content.encode("utf-8"))
        filepath = f.name

    # Restituisce il percorso del file
    yield filepath

    # Pulisce dopo il test
    os.unlink(filepath)


@pytest.fixture
def custom_sog_file():
    """Crea un file SOG con contenuto personalizzato usando polyfactory."""

    def _create_custom_file(num_soggetti=3, con_errori=False):
        with tempfile.NamedTemporaryFile(suffix=".SOG", delete=False) as f:
            records = SoggettiTestGenerator.genera_file_soggetti(
                num_soggetti=num_soggetti
            )

            # Se richiesto, introduci errori
            if con_errori:
                # Modifica il contenuto direttamente nel file invece di modificare i record
                # Questo permette di mantenere la validazione Pydantic ma avere un file con errori
                content = SoggettiTestGenerator.genera_file_content(records)
                # Sostituisce il tipo di soggetto P o G con un valore non valido M
                content = content.replace("|P|", "|M|").replace("|G|", "|M|")
                f.write(content.encode("utf-8"))
            else:
                content = SoggettiTestGenerator.genera_file_content(records)
                f.write(content.encode("utf-8"))

            filepath = f.name

        return filepath

    # Restituisce la funzione factory
    return _create_custom_file


@pytest.fixture
def random_titolarita():
    """Genera una titolarità casuale valida usando polyfactory."""
    return TitolaritaTestGenerator.genera_titolarita()


@pytest.fixture
def temp_tit_file():
    """Crea un file TIT temporaneo con dati casuali generati da polyfactory."""
    with tempfile.NamedTemporaryFile(suffix=".TIT", delete=False) as f:
        records = TitolaritaTestGenerator.genera_file_titolarita(num_titolarita=3)
        content = TitolaritaTestGenerator.genera_file_content(records)
        f.write(content.encode("utf-8"))
        filepath = f.name

    # Restituisce il percorso del file
    yield filepath

    # Pulisce dopo il test
    os.unlink(filepath)


@pytest.fixture
def custom_tit_file():
    """Crea un file TIT con contenuto personalizzato usando polyfactory."""

    def _create_custom_file(num_titolarita=3, con_errori=False):
        with tempfile.NamedTemporaryFile(suffix=".TIT", delete=False) as f:
            records = TitolaritaTestGenerator.genera_file_titolarita(
                num_titolarita=num_titolarita
            )

            # Se richiesto, introduci errori
            if con_errori:
                # Modifica il contenuto direttamente nel file invece di modificare i record
                # Questo permette di mantenere la validazione Pydantic ma avere un file con errori
                content = TitolaritaTestGenerator.genera_file_content(records)
                # Sostituisci il regime con un valore non valido
                content = content.replace("|C|", "|Z|").replace("|P|", "|Z|")
                f.write(content.encode("utf-8"))
            else:
                content = TitolaritaTestGenerator.genera_file_content(records)
                f.write(content.encode("utf-8"))

            filepath = f.name

        return filepath

    # Restituisce la funzione factory
    return _create_custom_file
