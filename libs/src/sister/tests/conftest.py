import pytest
import pathlib
import zipfile
from sister.archive import ArchiveService
from sister.storage import InMemoryArchiveStorage


directory = pathlib.Path("tests/data/")


@pytest.fixture
def sample_zip():
    with zipfile.ZipFile("tests/sample.zip", mode="w") as archive:
        for file_path in directory.iterdir():
            if file_path.suffix:
                archive.write(file_path, arcname=file_path.name)
        yield archive

@pytest.fixture
def mock_inmemory_archive_service(sample_zip):
    archive_service = ArchiveService(
        name="mock_archive",
        zip_file=sample_zip,
        archive_storage=InMemoryArchiveStorage()
    )
    yield archive_service
