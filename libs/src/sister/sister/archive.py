from typing import Protocol, List
from pathlib import Path
import tempfile

from .storage import ArchiveStorage


class Archive(Protocol):
    name: str
    zip_file: Path

    def store(self) -> None:
        pass

    def get_files(self) -> List[Path]:
        pass


class ArchiveService(Archive):
    _archive_storage: ArchiveStorage

    def __init__(
        self,
        name: str,
        zip_file: Path,
        archive_storage: ArchiveStorage
    ):
        self._name = name
        self._zip_file = zip_file
        self._archive_storage = archive_storage

    def store(self) -> None:
        self._archive_storage.save(files=self.get_files())

    def get_files(self) -> List[Path]:
        tmpdir = Path(tempfile.mkdtemp())
        with self._zip_file as zf:
            zf.extractall(tmpdir)
        return list(tmpdir.iterdir())
