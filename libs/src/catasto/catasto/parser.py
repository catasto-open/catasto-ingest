from typing import Protocol, Union
from .schemas.census import Census
from .schemas.carto import LandSheet
from .reader import (
    LocalFileReaderService,
    MinioFileReaderService
)


class FileParser(Protocol):

    reader: Union[
        LocalFileReaderService, MinioFileReaderService
    ]

    async def parse(self):
        pass


class FileParserService(FileParser):

    def __init__(
        self,
        reader: Union[
            LocalFileReaderService, MinioFileReaderService
        ]
    ):
        self._reader = reader

    async def parse(self) -> Union[Census, LandSheet]:
        async with self._reader.open() as _reader:
            filetype = _reader.filetype.upper()
            filename = _reader.filename.upper()
            content = _reader.content
            breakpoint()
            # parsing carto reader content
            if filetype in ["CXF", "CTF", "SUP"]:
                # parse filename
                # parse content
                _iter = iter(content.splitlines())
                for item in _iter:
                    result = None
                    # pass
            elif filetype in ["FAB", "TER", "SOG"]:
                result = Census(codice_comune="H501")
            yield result
