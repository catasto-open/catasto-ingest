import pytest
import pathlib
from catasto.reader import LocalFileReaderService
from catasto.parser import FileParserService
from catasto.schemas.common import ReaderFile


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
    breakpoint()
    return iter(content.splitlines())
