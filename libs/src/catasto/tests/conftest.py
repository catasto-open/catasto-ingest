import os
import pathlib
import tempfile

import pytest
from catasto.parser import FileParserService
from catasto.reader import LocalFileReaderService

from .fab_factory import (
    FabbricatiImmobileFactory,
    FabbricatiRecord1Factory,
    FabbricatiTestGenerator,
)

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


# --- Fixture per generazione di file fabbricati ---


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
                # Sostituisce una data valida con una invalida (32 come giorno)
                content = content.replace("01", "32", 1)
                f.write(content.encode("utf-8"))
            else:
                content = FabbricatiTestGenerator.genera_file_content(records)
                f.write(content.encode("utf-8"))

            filepath = f.name

        return filepath

    # Restituisce la funzione factory
    return _create_custom_file


@pytest.fixture
def immobile_factory():
    """Fixture che restituisce una factory di immobili per uso personalizzato nei test."""
    return FabbricatiImmobileFactory
