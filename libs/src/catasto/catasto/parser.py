import logging
from typing import Dict, Iterator, Protocol, Tuple, Union

from .reader import LocalFileReaderService, MinioFileReaderService
from .schemas.carto import CartoObject, HeaderModel, LandSheet
from .schemas.census import Census

# Configurazione del logger
logger = logging.getLogger(__name__)


class FileParser(Protocol):
    reader: Union[LocalFileReaderService, MinioFileReaderService]

    async def parse(self):
        pass


class FileParserService(FileParser):
    def __init__(self, reader: Union[LocalFileReaderService, MinioFileReaderService]):
        self._reader = reader

    async def parse(self) -> Union[Census, LandSheet]:
        async with self._reader.open() as _reader:
            filetype = _reader.filetype.upper() if _reader.filetype else ""
            filename = _reader.filename.upper() if _reader.filename else ""
            content = _reader.content or ""
            name = filename.replace(filetype, "")

            # Validazione input base
            if not filetype or not filename or not content:
                logger.error(
                    f"Dati di input non validi: \
                        filetype={filetype}, \
                        filename={filename}, \
                        content_length={len(content)}"
                )
                return None

            # parsing carto reader content
            if filetype in [".CXF", ".CTF"]:
                try:
                    carto = LandSheet()
                    # parse filename
                    carto = self._parse_carto_filename(carto, name)
                    # parse content
                    gen_lines = iter(content.splitlines())
                    carto.header = HeaderModel()
                    carto, gen_lines = self._parse_carto_fileheader(carto, gen_lines)
                    carto = self._parse_carto_objects(carto, gen_lines)
                    result = carto
                except Exception as e:
                    logger.error(f"Errore durante il parsing cartografico: {str(e)}")
                    raise
            # Parsing dei file censuari (FAB, TER, SOG, TIT, ecc.)
            elif filetype in [".FAB", ".TER", ".SOG", ".TIT"]:
                try:
                    # Estrai il codice comune dal nome del file
                    codice_comune = self._extract_codice_comune(name)

                    # Inizializza l'oggetto Census
                    census = Census(codice_comune=codice_comune)

                    # Ottieni il percorso base per accedere agli altri file
                    # basepath = os.path.splitext(_reader.filepath)[0]

                    # Elabora il file principale
                    self._parse_census_file(census, filetype, content)

                    # Se il file principale è FAB, TER o SOG, cerca di elaborare anche gli altri file correlati
                    # if filetype in [".FAB", ".TER", ".SOG"]:
                    #     self._process_related_census_files(census, basepath, filetype)

                    result = census
                except Exception as e:
                    logger.error(
                        f"Errore durante il parsing dei file di censuario: {str(e)}"
                    )
                    raise
            elif filetype in [".SUP"]:
                logger.info(f"Parsing del formato {filetype} non ancora implementato")
                result = None
            else:
                logger.warning(f"Tipo di file non supportato: {filetype}")
                result = None
            return result

    def _parse_carto_filename(self, land_sheet: LandSheet, name: str) -> LandSheet:
        land_sheet.codice_foglio = name
        land_sheet.codice_comune = name[:4]
        land_sheet.codice_sezione_censuaria = name[4]
        land_sheet.codice_numero_foglio = name[5:9]
        land_sheet.numero_foglio = name[5:9].lstrip("0")
        land_sheet.codice_allegato = name[9]
        land_sheet.codice_sviluppo = name[10]
        return land_sheet

    def _parse_carto_fileheader(
        self, land_sheet: LandSheet, _iter: Iterator
    ) -> Tuple[LandSheet, Iterator]:
        header = HeaderModel()
        header.mappa = next(_iter).strip()
        header.nome_mappa = next(_iter).strip()
        header.scala_originaria = next(_iter).strip()
        land_sheet.header = header
        return (land_sheet, _iter)

    def _parse_carto_objects(
        self, land_sheet: LandSheet, _iter: Iterator
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
                obj["VERTICI"].append((next(_iter).strip(), next(_iter).strip()))
            return obj

        def _get_tabisole(_iter: Iterator, obj: Dict) -> Dict:
            obj["TABISOLE"] = []
            for item in range(int(obj["NUMEROISOLE"])):
                obj["TABISOLE"].append(next(_iter).strip())
            return obj

        def _build_carto_objects(tipo=None, vertici=None, tabisole=None) -> Dict:
            carto_objects = {
                "BORDO": (
                    [
                        "CODICE_IDENTIFICATIVO",
                        "DIMENSIONE",
                        "ANGOLO",
                        "POSIZIONEX",
                        "POSIZIONEY",
                        "PUNTOINTERNOX",
                        "PUNTOINTERNOY",
                        "NUMEROISOLE",
                        "NUMEROVERTICI",
                    ],
                    ["tabisole", "vertici", "tipo"],
                ),
                "TESTO": (
                    ["TESTO", "DIMENSIONE", "ANGOLO", "POSIZIONEX", "POSIZIONEY"],
                    [],
                ),
                "SIMBOLO": (
                    ["CODICE SIMBOLO", "ANGOLO", "POSIZIONEX", "POSIZIONEY"],
                    [],
                ),
                "FIDUCIALE": (
                    [
                        "NUMERO_IDENTIFICATIVO",
                        "CODICE SIMBOLO",
                        "POSIZIONEX",
                        "POSIZIONEY",
                        "PUNTORAPPRESENTAZIONEX",
                        "PUNTORAPPRESENTAZIONEY",
                    ],
                    [],
                ),
                "LINEA": (["CODICE TIPO DI TRATTO", "NUMEROVERTICI"], ["vertici"]),
                "EOF": ([], []),
            }
            return carto_objects

        land_sheet.oggetti = CartoObject()
        for raw_line in _iter:
            line = raw_line.strip().rstrip("\\")
            if line not in land_sheet.oggetti.model_dump(by_alias=True):
                raise ValueError(f"Unkwown object {line}")
            obj = {}
            record_names, functions = _build_carto_objects()[line]
            for record_name in record_names:
                obj[record_name] = next(_iter).strip()
            for function in functions:
                if function == "tipo":
                    obj = _get_tipo(_iter=_iter, obj=obj)
                elif function == "vertici":
                    obj = _get_vertici(_iter=_iter, obj=obj)
                elif function == "tabisole":
                    obj = _get_tabisole(_iter=_iter, obj=obj)
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

    def _extract_codice_comune(self, name: str) -> str:
        """
        Estrae il codice comune dal nome del file.

        Args:
            name: Il nome del file senza estensione

        Returns:
            str: Il codice comune
        """
        # Verifica che il nome del file abbia una lunghezza valida
        valid_lengths = [7, 8, 10, 11, 12, 13, 14]
        if len(name) not in valid_lengths:
            logger.warning(
                f"Lunghezza nome file non standard: {len(name)}, nome: {name}"
            )
            # Se il nome non è standard, tenta comunque di estrarre i primi 4 caratteri
            return name[:4] if len(name) >= 4 else "0000"

        # I primi 4 caratteri sono il codice comune
        return name[:4]

    def _parse_census_filename(
        self, census: Census, filetype: str, content: str = None
    ) -> None:
        """
        Parse il file censuario specificato e aggiorna l'oggetto Census.

        Args:
            census: L'oggetto Census da aggiornare
            filetype: Il tipo di file da parsare (.FAB, .TER, .SOG, .TIT)
            basepath: Il percorso base del file
            content: Il contenuto del file (se già caricato)
        """
        if filetype == ".FAB":
            self._parse_fab_file(census, content)
        elif filetype == ".TER":
            self._parse_ter_file(census, content)
        elif filetype == ".SOG":
            self._parse_sog_file(census, content)
        elif filetype == ".TIT":
            self._parse_tit_file(census, content)
        else:
            logger.warning(
                f"Tipo di file non supportato per il parsing censuario: {filetype}"
            )
