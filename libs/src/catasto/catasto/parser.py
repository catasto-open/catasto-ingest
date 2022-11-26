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
            name = filename.replace(filetype, "")
            # parsing carto reader content
            carto = LandSheet()
            if filetype in [".CXF", ".CTF", ".SUP"]:
                # parse filename
                carto = self._parse_name(carto, name)
                # parse content
                _iter = iter(content.splitlines())
                for item in _iter:
                    # breakpoint()
                    result = carto
                    # pass
            elif filetype in ["FAB", "TER", "SOG"]:
                result = Census(codice_comune="H501")
            return result

    def _parse_name(self, land_sheet: LandSheet, name: str) -> LandSheet:
        land_sheet.codice_foglio = name
        land_sheet.codice_comune = name[:4]
        land_sheet.codice_sezione_censuaria = name[4]
        land_sheet.codice_numero_foglio = name[5:9]
        land_sheet.numero_foglio = name[5:9].lstrip("0")
        land_sheet.codice_allegato = name[9]
        land_sheet.codice_sviluppo = name[10]
        return land_sheet
