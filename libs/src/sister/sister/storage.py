from typing import Protocol, List, Union
from shutil import copyfile
from pathlib import Path
import tempfile


class ArchiveStorage(Protocol):
    _location: Union[str, None]

    def save(files: List[Path]):
        pass


class InMemoryArchiveStorage(ArchiveStorage):
    def __init__(self):
        self._location = tempfile.mkdtemp()
        self._tmpdir = Path(self._location)

    def save(self, files: List[Path]) -> None:
        tmpdir = self._tmpdir
        for file in files:
            tmp_file = tmpdir / file.name
            copyfile(file, tmp_file)

    def __del__(self):
        for file in [
            item for item in self._tmpdir.iterdir() if item.is_file()
        ]:
            file.unlink()
        self._tmpdir.rmdir()
