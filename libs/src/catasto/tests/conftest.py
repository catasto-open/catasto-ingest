import pytest
import pathlib
from catasto.reader import LocalFileReaderService


directory = pathlib.Path("tests/data/")


@pytest.fixture
def local_file():
    _file = directory / "textfile.SOG"
    return _file.absolute().__str__()


@pytest.fixture
def local_dir():
    _dir = directory
    return _dir.absolute().__str__()


@pytest.fixture
def local_file_reader(local_file):
    return LocalFileReaderService(filepath=local_file)


@pytest.fixture
def local_dir_reader(local_dir):
    return LocalFileReaderService(filepath=local_dir)
