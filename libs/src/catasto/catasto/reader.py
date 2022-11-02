from typing import Protocol
from pathlib import Path
import aiofiles
from .schemas.common import ReaderFile


class Reader(Protocol):

    filepath: str

    async def open(self) -> ReaderFile:
        pass

    def validate(self) -> bool:
        pass


class LocalFileReaderService(Reader):

    def __init__(self, filepath: str):
        self._filepath = filepath

    async def open(self) -> str:
        _filepath = Path(self._filepath)
        filename = _filepath.name
        filetype = _filepath.suffix
        if not _filepath.is_file():
            raise ValueError("Filepath is not a file")
        if not self.validate():
            raise ValueError(
                f"File type {filetype} is not valid"
            )
        async with aiofiles.open(_filepath, 'r') as _file:
            content = await _file.read()
            return ReaderFile(
                filename=filename,
                filetype=filetype,
                content=content
            )

    def validate(self) -> bool:
        # @TODO: validate the file extension
        return True
