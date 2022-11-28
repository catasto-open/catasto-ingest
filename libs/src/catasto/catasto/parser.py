from typing import (
    Protocol, Union, Tuple, Iterator,  Dict
)
from .schemas.census import Census
from .schemas.carto import (
    LandSheet, HeaderModel, CartoObjectItem,
    CartoObject
)
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
            if filetype in [".CXF", ".CTF"]:
                try:
                    # parse filename
                    carto = self._parse_name(carto, name)
                    # parse content
                    gen_lines = iter(content.splitlines())
                    carto.header = HeaderModel()
                    carto, gen_lines = self._parse_header(carto, gen_lines)
                    carto = self._parse_objects(carto, gen_lines)
                    result = carto
                    # breakpoint()
                except Exception as e:
                    print(e)
            elif filetype in [".SUP"]:
                pass
            elif filetype in [".FAB", ".TER", ".SOG"]:
                result = Census(codice_comune="H501")
            return result

    def _parse_name(
        self,
        land_sheet: LandSheet,
        name: str
    ) -> LandSheet:
        land_sheet.codice_foglio = name
        land_sheet.codice_comune = name[:4]
        land_sheet.codice_sezione_censuaria = name[4]
        land_sheet.codice_numero_foglio = name[5:9]
        land_sheet.numero_foglio = name[5:9].lstrip("0")
        land_sheet.codice_allegato = name[9]
        land_sheet.codice_sviluppo = name[10]
        return land_sheet

    def _parse_header(
        self,
        land_sheet: LandSheet,
        _iter: Iterator
    ) -> Tuple[LandSheet, Iterator]:
        header = HeaderModel()
        header.mappa = next(_iter).strip()
        header.nome_mappa = next(_iter).strip()
        header.scala_originaria = next(_iter).strip()
        land_sheet.header = header
        return (land_sheet, _iter)

    def _parse_objects(
        self,
        land_sheet: LandSheet,
        _iter: Iterator
    ) -> Tuple[LandSheet, Iterator]:

        def _get_tipo(_iter: Iterator, obj: Dict) -> Dict:
            obj["TIPO"] = []
            if len(obj["CODICE_IDENTIFICATIVO"]) == 11:
                tipo = "CONFINE"
            elif obj["CODICE_IDENTIFICATIVO"] == "STRADA":
                tipo = "STRADA"
            elif obj["CODICE_IDENTIFICATIVO"] == "ACQUA":
                tipo = "ACQUA"
            elif obj["CODICE_IDENTIFICATIVO"][-1] == "+":
                tipo = "FABBRICATO"
            else:
                tipo = "PARTICELLA"
            obj["TIPO"] = tipo
            return obj

        def _get_vertici(_iter: Iterator, obj: Dict) -> Dict:
            obj["VERTICI"] = []
            for item in range(int(obj["NUMEROVERTICI"])):
                obj["VERTICI"].append((
                    next(_iter).strip(),
                    next(_iter).strip()
                ))
            return obj

        def _get_tabisole(_iter: Iterator, obj: Dict) -> Dict:
            obj["TABISOLE"] = []
            for item in range(int(obj["NUMEROISOLE"])):
                obj["TABISOLE"].append(next(_iter).strip())
            return obj

        def _build_carto_objects(
            tipo=None,
            vertici=None,
            tabisole=None
        ) -> Dict:
            carto_objects = {
                "BORDO": (
                    [
                        "CODICE_IDENTIFICATIVO", "DIMENSIONE", "ANGOLO",
                        "POSIZIONEX", "POSIZIONEY", "PUNTOINTERNOX",
                        "PUNTOINTERNOY", "NUMEROISOLE", "NUMEROVERTICI"
                    ],
                    [
                        "tabisole", "vertici", "tipo"
                    ]
                ),
                "TESTO": (
                    [
                        "TESTO", "DIMENSIONE", "ANGOLO",
                        "POSIZIONEX", "POSIZIONEY"
                    ],
                    []
                ),
                "SIMBOLO": (
                    [
                        "CODICE SIMBOLO", "ANGOLO", "POSIZIONEX",
                        "POSIZIONEY"
                    ],
                    []
                ),
                "FIDUCIALE": (
                    [
                        "NUMERO_IDENTIFICATIVO", "CODICE SIMBOLO",
                        "POSIZIONEX", "POSIZIONEY", "PUNTORAPPRESENTAZIONEX",
                        "PUNTORAPPRESENTAZIONEY"
                    ],
                    []
                ),
                "LINEA": (
                    [
                        "CODICE TIPO DI TRATTO", "NUMEROVERTICI"
                    ],
                    [
                        "vertici"
                    ]
                ),
                "EOF": (
                    [],
                    []
                ),
            }
            return carto_objects

        land_sheet.oggetti = CartoObject()
        for raw_line in _iter:
            line = raw_line.strip().rstrip('\\')
            if line not in land_sheet.oggetti.dict(by_alias=True):
                raise ValueError(f"Unkwown object {line}")
            obj = {}
            record_names, functions = _build_carto_objects()[line]
            for record_name in record_names:
                obj[record_name] = next(_iter).strip()
            for function in functions:
                if function == "tipo":
                    obj = _get_tipo(_iter=_iter, obj=obj)
                elif function == "vertici":
                    obj = _get_vertici(
                        _iter=_iter,
                        obj=obj
                    )
                elif function == "tabisole":
                    obj = _get_tabisole(
                        _iter=_iter,
                        obj=obj
                    )
            if line == "BORDO":
                land_sheet.oggetti.bordo.append(obj)
            elif line == "TESTO":
                land_sheet.oggetti.testo.append(obj)
            elif line == "SIMBOLO":
                land_sheet.oggetti.simbolo.append(obj)
            elif line == "FIDUCIALE":
                land_sheet.oggetti.fiduciale.append(obj)
            elif line == "LINEA":
                land_sheet.oggetti.linea.append(obj)
            elif line == "EOF":
                # exit record
                break
            else:
                pass
        try:
            garbage = next(_iter)
        except StopIteration:
            garbage = None
        if garbage is not None:
            print(f"Garbage after CTF EOF {garbage}")
        return land_sheet