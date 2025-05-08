from sister import __version__
from sister.storage import InMemoryArchiveStorage
from pathlib import Path


def test_version():
    assert __version__ == '0.1.0'

def test_archive_get_files(mock_inmemory_archive_service):
    files = mock_inmemory_archive_service.get_files()
    for file in files:
        assert file.name in ["sample_rieti.txt", "sample_roma.txt"]

def test_archive_inmemory_store(mock_inmemory_archive_service):
    mock_inmemory_archive_service.store()
    pathdir = Path(
        mock_inmemory_archive_service._archive_storage._location
    )
    assert pathdir.exists()
    assert pathdir.is_dir()
    files = [item for item in pathdir.iterdir() if item.is_file()]
    for file in files:
        assert file.name in ["sample_rieti.txt", "sample_roma.txt"]

def test_archive_inmemory_cleanup():
    inmemory_archive_service = InMemoryArchiveStorage()
    pathdir = inmemory_archive_service._tmpdir

    del inmemory_archive_service
    assert not pathdir.exists()
