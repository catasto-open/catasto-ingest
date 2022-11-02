from typing import Protocol, Union
from .schemas.census import Census
from .reader import (
    LocalFileReaderService,
    RemoteFileReaderService
)


class FileParser(Protocol):

    filename: Union[
        LocalFileReaderService, RemoteFileReaderService
    ]

    async def parse(self):
        pass


class FileParserService(FileParser):

    def __init__(
        self,
        filename: Union[
            LocalFileReaderService, RemoteFileReaderService
        ]
    ):
        self._filename = filename

    async def parse(self) -> Census:
        async with self._filename.open() as _file:
            return Census(codice_comune="H501")