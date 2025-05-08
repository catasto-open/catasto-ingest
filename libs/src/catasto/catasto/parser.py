import logging
from typing import Dict, Iterator, Protocol, Tuple, Union

from pydantic import ValidationError

from .reader import LocalFileReaderService, MinioFileReaderService
from .schemas.building import (
    FabbricatiImmobile,
    FabbricatiModel,
    FabbricatiRecord1,
    FabbricatiRecord2,
    FabbricatiRecord3,
    FabbricatiRecord4,
    FabbricatiRecord5,
    FabRecordInfo,
    Identificativo,
    Indirizzo,
    UtilitaComune,
)
from .schemas.building import Riserva as BuildingRiserva
from .schemas.carto import CartoHeaderModel, CartoObject, LandSheet
from .schemas.census import Census
from .schemas.entitlement import (
    TipoImmobileEnum,
    TipoRegimeEnum,
    TipoSoggettoEnum,
    Titolarita,
    TitolaritaModel,
    TitRecordInfo,
)
from .schemas.land import (
    Deduzione,
    PorzioneSdi,
    TerRecordInfo,
    TerreniImmobile,
    TerreniModel,
    TerreniRecord1,
    TerreniRecord2,
    TerreniRecord3,
    TerreniRecord4,
)
from .schemas.land import Riserva as LandRiserva
from .schemas.subject import (
    SoggettiModel,
    SoggettiRecordGiuridicPerson,
    SoggettiRecordPrivatePerson,
    Soggetto,
    SogRecordInfo,
)

# Configurazione del logger
logger = logging.getLogger(__name__)


class ParsingError(Exception):
    """Eccezione sollevata per errori nel parsing dei file catastali."""

    def __init__(self, message, errors=None):
        super().__init__(message)
        self.errors = errors or []

    def __str__(self):
        if not self.errors:
            return super().__str__()
        return f"{super().__str__()}:\n" + "\n".join(self.errors)


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
                    carto.header = CartoHeaderModel()
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
                    self._parse_census_filename(census, filetype, content)

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
        header = CartoHeaderModel()
        header.mappa = next(_iter).strip()
        header.nome_mappa = next(_iter).strip()
        header.scala_originaria = next(_iter).strip()
        land_sheet.header = header
        return (land_sheet, _iter)

    def _parse_carto_objects(self, land_sheet: LandSheet, _iter: Iterator) -> LandSheet:
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
            raw_line = raw_line.strip()
            is_external = False

            # Controlla se l'elemento è esterno (ha il '\' alla fine)
            if raw_line.endswith("\\"):
                is_external = True
                line = raw_line.rstrip("\\")
            else:
                line = raw_line

            if line not in land_sheet.oggetti.model_dump(by_alias=True):
                raise ValueError(f"Unkwown object {line}")

            obj = {}
            # Aggiungi questa informazione all'oggetto
            obj["ESTERNO"] = is_external

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

    def _parse_fab_file(self, census: Census, content: str) -> None:
        """
        Parsifica un file .FAB e aggiorna l'oggetto Census con i dati di fabbricati.

        Args:
            census: L'oggetto Census da aggiornare
            content: Il contenuto del file FAB

        Raises:
            ValueError: Se il file è vuoto o malformato
            ValidationError: Se i dati non rispettano i vincoli dei modelli
            ParsingError: Se ci sono errori durante il parsing
        """
        if not content:
            raise ValueError("Contenuto del file FAB vuoto o non valido")
        # Inizializza il modello FabbricatiModel se non esiste già
        if not census.fabbricati:
            census.fabbricati = FabbricatiModel()

        # Errori accumulati durante il parsing
        errors = []

        try:
            # Organizziamo i record per immobile
            record_groups = {}
            # Processa ogni linea
            for line_num, line in enumerate(content.splitlines(), 1):
                if not line:
                    continue

                try:
                    # Estrai le informazioni di base
                    record_info = self._parse_fab_record_info(line)
                    key = (
                        record_info.codice_amministrativo,
                        record_info.sezione,
                        record_info.identificativo_immobile,
                        record_info.tipo_immobile,
                        record_info.progressivo,
                    )

                    # Se è un nuovo immobile, inizializza il dizionario
                    if key not in record_groups:
                        record_groups[key] = {}

                    # Aggiungi il record al dizionario dell'immobile
                    record_groups[key][record_info.tipo_record] = record_info.raw_line

                except Exception as e:
                    # Accumula l'errore
                    errors.append(f"Errore alla riga {line_num}: {str(e)}")

            # Solleva un'eccezione se ci sono stati errori durante il parsing delle righe
            if errors:
                print(errors)
                raise ParsingError("Errori nel parsing del file FAB", errors)

            # Processa ogni gruppo di record per creare immobili
            for key, records in record_groups.items():
                try:
                    # Verifica che ci siano i record obbligatori
                    if "1" not in records.keys():
                        errors.append(
                            f"Immobile {key}: manca il record di tipo 1 (obbligatorio)"
                        )
                        continue

                    if "2" not in records.keys():
                        errors.append(
                            f"Immobile {key}: manca il record di tipo 2 (obbligatorio)"
                        )
                        continue

                    # Crea l'immobile
                    immobile = self._parse_fab_immobile(key, records)

                    # Aggiungi l'immobile al census
                    census.fabbricati.add_immobile(immobile)

                except Exception as e:
                    errors.append(f"Errore nel parsing dell'immobile {key}: {str(e)}")

            # Solleva un'eccezione se ci sono stati errori nel parsing degli immobili
            if errors:
                raise ParsingError("Errori nel parsing del file FAB", errors)

            # Se non ci sono immobili, potrebbe essere un problema
            if not census.fabbricati.immobili:
                logger.warning("Nessun immobile trovato nel file FAB")

        except ParsingError:
            # Rilanciamo l'eccezione ParsingError senza modificarla
            logger.error("Errori durante il parsing del file FAB")
            raise

        except Exception as e:
            # Per altre eccezioni, le convertiamo in ParsingError
            logger.error(
                f"Errore non previsto durante il parsing del file FAB: {str(e)}"
            )
            raise ParsingError(f"Errore durante il parsing del file FAB: {str(e)}")

    def _parse_fab_record_info(self, line: str) -> FabRecordInfo:
        """
        Estrae le informazioni di base da una riga del file FAB.

        Args:
            line: La riga del file FAB

        Returns:
            FabRecordInfo: Le informazioni estratte

        Raises:
            ValueError: Se la riga è malformata
        """

        try:
            parser = parse_fab_record_info(line=line)
            return parser
        except Exception:
            raise

    def _parse_fab_immobile(
        self, key: tuple, records: Dict[str, str]
    ) -> FabbricatiImmobile:
        """
        Crea un oggetto FabbricatiImmobile dai record estratti.

        Args:
            key: Tupla che identifica l'immobile
            records: Dizionario dei record per tipo

        Returns:
            FabbricatiImmobile: L'oggetto immobile creato

        Raises:
            ValueError: Se mancano i record obbligatori o se ci sono errori nei record
        """

        # Estrai i dati dalla chiave
        (
            codice_amministrativo,
            sezione,
            identificativo_immobile,
            tipo_immobile,
            progressivo,
        ) = key

        # Crea i record specifici
        record1 = self._parse_fab_record1_line(records["1"])
        record2 = self._parse_fab_record2_line(records["2"])

        # Record opzionali
        record3 = self._parse_fab_record3_line(records["3"]) if "3" in records else None
        record4 = self._parse_fab_record4_line(records["4"]) if "4" in records else None
        record5 = self._parse_fab_record5_line(records["5"]) if "5" in records else None

        # Crea e restituisci l'oggetto immobile
        return FabbricatiImmobile(
            codice_amministrativo=codice_amministrativo,
            sezione=sezione,
            identificativo_immobile=identificativo_immobile,
            tipo_immobile=tipo_immobile,
            progressivo=progressivo,
            record1=record1,
            record2=record2,
            record3=record3,
            record4=record4,
            record5=record5,
        )

    def _parse_fab_record1_line(self, line: str) -> FabbricatiRecord1:
        """
        Parsifica una riga di record di tipo 1.

        Args:
            line: La riga del record

        Returns:
            FabbricatiRecord1: L'oggetto record creato

        Raises:
            ValueError: Se la riga è malformata
            ValidationError: Se i dati non rispettano i vincoli del modello
        """

        record_info = parse_fab_record_info(line=line)
        parser = parse_fab_record1_line(record=record_info)

        return parser

    def _parse_fab_record2_line(self, line: str) -> FabbricatiRecord2:
        """
        Parsifica una riga di record di tipo 2.

        Args:
            line: La riga del record

        Returns:
            FabbricatiRecord2: L'oggetto record creato

        Raises:
            ValueError: Se la riga è malformata
            ValidationError: Se i dati non rispettano i vincoli del modello
        """

        record_info = parse_fab_record_info(line=line)
        parser = parse_fab_record2_line(record=record_info)

        return parser

    def _parse_fab_record3_line(self, line: str) -> FabbricatiRecord3:
        """
        Parsifica una riga di record di tipo 3.

        Args:
            line: La riga del record

        Returns:
            FabbricatiRecord3: L'oggetto record creato

        Raises:
            ValueError: Se la riga è malformata
            ValidationError: Se i dati non rispettano i vincoli del modello
        """

        record_info = parse_fab_record_info(line=line)
        parser = parse_fab_record3_line(record=record_info)

        return parser

    def _parse_fab_record4_line(self, line: str) -> FabbricatiRecord4:
        """
        Parsifica una riga di record di tipo 4.

        Args:
            line: La riga del record

        Returns:
            FabbricatiRecord4: L'oggetto record creato

        Raises:
            ValueError: Se la riga è malformata
            ValidationError: Se i dati non rispettano i vincoli del modello
        """

        record_info = parse_fab_record_info(line=line)
        parser = parse_fab_record4_line(record=record_info)

        return parser

    def _parse_fab_record5_line(self, line: str) -> FabbricatiRecord5:
        """
        Parsifica una riga di record di tipo 5.

        Args:
            line: La riga del record

        Returns:
            FabbricatiRecord5: L'oggetto record creato

        Raises:
            ValueError: Se la riga è malformata
            ValidationError: Se i dati non rispettano i vincoli del modello
        """

        record_info = parse_fab_record_info(line=line)
        parser = parse_fab_record5_line(record=record_info)

        return parser

    def _parse_ter_file(self, census: Census, content: str) -> None:
        """
        Parsifica un file .TER e aggiorna l'oggetto Census con i dati di fabbricati.

        Args:
            census: L'oggetto Census da aggiornare
            content: Il contenuto del file TER

        Raises:
            ValueError: Se il file è vuoto o malformato
            ValidationError: Se i dati non rispettano i vincoli dei modelli
            ParsingError: Se ci sono errori durante il parsing
        """
        if not content:
            raise ValueError("Contenuto del file TER vuoto o non valido")
        # Inizializza il modello TerreniModel se non esiste già
        if not census.terreni:
            census.terreni = TerreniModel()

        # Errori accumulati durante il parsing
        errors = []

        try:
            # Organizziamo i record per immobile
            record_groups = {}
            # Processa ogni linea
            for line_num, line in enumerate(content.splitlines(), 1):
                if not line:
                    continue

                try:
                    # Estrai le informazioni di base
                    record_info = self._parse_ter_record_info(line)
                    key = (
                        record_info.codice_amministrativo,
                        record_info.sezione,
                        record_info.identificativo_immobile,
                        record_info.tipo_immobile,
                        record_info.progressivo,
                    )

                    # Se è un nuovo immobile, inizializza il dizionario
                    if key not in record_groups:
                        record_groups[key] = {}

                    # Aggiungi il record al dizionario dell'immobile
                    record_groups[key][record_info.tipo_record] = record_info.raw_line

                except Exception as e:
                    # Accumula l'errore
                    errors.append(f"Errore alla riga {line_num}: {str(e)}")

            # Solleva un'eccezione se ci sono stati errori durante il parsing delle righe
            if errors:
                print(errors)
                raise ParsingError("Errori nel parsing del file TER", errors)

            # Processa ogni gruppo di record per creare immobili
            for key, records in record_groups.items():
                try:
                    # Verifica che ci siano i record obbligatori
                    if "1" not in records.keys():
                        errors.append(
                            f"Immobile {key}: manca il record di tipo 1 (obbligatorio)"
                        )
                        continue

                    # Crea l'immobile
                    immobile = self._parse_ter_immobile(key, records)

                    # Aggiungi l'immobile al census
                    census.terreni.add_immobile(immobile)

                except Exception as e:
                    errors.append(f"Errore nel parsing dell'immobile {key}: {str(e)}")

            # Solleva un'eccezione se ci sono stati errori nel parsing degli immobili
            if errors:
                raise ParsingError("Errori nel parsing del file TER", errors)

            # Se non ci sono immobili, potrebbe essere un problema
            if not census.terreni.immobili:
                logger.warning("Nessun immobile trovato nel file TER")

        except ParsingError:
            # Rilanciamo l'eccezione ParsingError senza modificarla
            logger.error("Errori durante il parsing del file TER")
            raise

        except Exception as e:
            # Per altre eccezioni, le convertiamo in ParsingError
            logger.error(
                f"Errore non previsto durante il parsing del file TER: {str(e)}"
            )
            raise ParsingError(f"Errore durante il parsing del file : {str(e)}")

    def _parse_ter_record_info(self, line: str) -> TerRecordInfo:
        """
        Estrae le informazioni di base da una riga del file TER.

        Args:
            line: La riga del file TER

        Returns:
            TerRecordInfo: Le informazioni estratte

        Raises:
            ValueError: Se la riga è malformata
        """

        try:
            parser = parse_ter_record_info(line=line)
            return parser
        except Exception:
            raise

    def _parse_ter_immobile(
        self, key: tuple, records: Dict[str, str]
    ) -> TerreniImmobile:
        """
        Crea un oggetto TerreniImmobile dai record estratti.

        Args:
            key: Tupla che identifica l'immobile
            records: Dizionario dei record per tipo

        Returns:
            TerreniImmobile: L'oggetto immobile creato

        Raises:
            ValueError: Se mancano i record obbligatori o se ci sono errori nei record
        """

        # Estrai i dati dalla chiave
        (
            codice_amministrativo,
            sezione,
            identificativo_immobile,
            tipo_immobile,
            progressivo,
        ) = key

        # Crea i record specifici
        record1 = self._parse_ter_record1_line(records["1"])

        # Record opzionali
        record2 = self._parse_ter_record2_line(records["2"]) if "2" in records else None
        record3 = self._parse_ter_record3_line(records["3"]) if "3" in records else None
        record4 = self._parse_ter_record4_line(records["4"]) if "4" in records else None

        # Crea e restituisci l'oggetto immobile
        return TerreniImmobile(
            codice_amministrativo=codice_amministrativo,
            sezione=sezione,
            identificativo_immobile=identificativo_immobile,
            tipo_immobile=tipo_immobile,
            progressivo=progressivo,
            record1=record1,
            record2=record2,
            record3=record3,
            record4=record4,
        )

    def _parse_ter_record1_line(self, line: str) -> TerreniRecord1:
        """
        Parsifica una riga di record di tipo 1.

        Args:
            line: La riga del record

        Returns:
            TerreniRecord1: L'oggetto record creato

        Raises:
            ValueError: Se la riga è malformata
            ValidationError: Se i dati non rispettano i vincoli del modello
        """

        record_info = parse_ter_record_info(line=line)
        parser = parse_ter_record1_line(record=record_info)

        return parser

    def _parse_ter_record2_line(self, line: str) -> TerreniRecord2:
        """
        Parsifica una riga di record di tipo 2.

        Args:
            line: La riga del record

        Returns:
            TerreniRecord2: L'oggetto record creato

        Raises:
            ValueError: Se la riga è malformata
            ValidationError: Se i dati non rispettano i vincoli del modello
        """

        record_info = parse_ter_record_info(line=line)
        parser = parse_ter_record2_line(record=record_info)

        return parser

    def _parse_ter_record3_line(self, line: str) -> TerreniRecord3:
        """
        Parsifica una riga di record di tipo 3.

        Args:
            line: La riga del record

        Returns:
            TerreniRecord3: L'oggetto record creato

        Raises:
            ValueError: Se la riga è malformata
            ValidationError: Se i dati non rispettano i vincoli del modello
        """

        record_info = parse_ter_record_info(line=line)
        parser = parse_ter_record3_line(record=record_info)

        return parser

    def _parse_ter_record4_line(self, line: str) -> TerreniRecord4:
        """
        Parsifica una riga di record di tipo 4.

        Args:
            line: La riga del record

        Returns:
            TerreniRecord4: L'oggetto record creato

        Raises:
            ValueError: Se la riga è malformata
            ValidationError: Se i dati non rispettano i vincoli del modello
        """

        record_info = parse_ter_record_info(line=line)
        parser = parse_ter_record4_line(record=record_info)

        return parser

    def _parse_sog_file(self, census: Census, content: str) -> None:
        """
        Parsifica un file .SOG e aggiorna l'oggetto Census con i dati degli intestati/soggetti.

        Args:
            census: L'oggetto Census da aggiornare
            content: Il contenuto del file SOG

        Raises:
            ValueError: Se il file è vuoto o malformato
            ValidationError: Se i dati non rispettano i vincoli dei modelli
            ParsingError: Se ci sono errori durante il parsing
        """
        if not content:
            raise ValueError("Contenuto del file SOG vuoto o non valido")
        # Inizializza il modello SoggettiModel se non esiste già
        if not census.soggetti:
            census.soggetti = SoggettiModel()

        # Errori accumulati durante il parsing
        errors = []

        try:
            # Organizziamo i record per soggetto
            record_groups = {}
            # Processa ogni linea
            for line_num, line in enumerate(content.splitlines(), 1):
                if not line:
                    continue

                try:
                    # Estrai le informazioni di base
                    record_info = self._parse_sog_record_info(line)
                    key = (
                        record_info.codice_amministrativo,
                        record_info.sezione,
                        record_info.identificativo_soggetto,
                        record_info.tipo_soggetto,
                    )

                    # Se è un nuovo immobile, inizializza il dizionario
                    if key not in record_groups:
                        record_groups[key] = {}

                    # Aggiungi il record al dizionario del soggetto
                    record_groups[key][record_info.tipo_soggetto] = record_info.raw_line

                except Exception as e:
                    # Accumula l'errore
                    errors.append(f"Errore alla riga {line_num}: {str(e)}")

            # Solleva un'eccezione se ci sono stati errori durante il parsing delle righe
            if errors:
                print(errors)
                raise ParsingError("Errori nel parsing del file SOG", errors)

            # Processa ogni gruppo di record per creare soggetti
            for key, records in record_groups.items():
                try:
                    # Verifica che ci sia almeno uno dei record obbligatori (P o G)
                    if "P" not in records.keys() and "G" not in records.keys():
                        errors.append(
                            f"Soggetto {key}: manca il record di tipo P o G (obbligatorio)"
                        )
                        continue

                    # Verifica che non ci siano entrambi i tipi di record (P e G)
                    if "P" in records.keys() and "G" in records.keys():
                        errors.append(
                            f"Soggetto {key}: non può avere sia il record di tipo P che di tipo G"
                        )
                        continue

                    # Crea il soggetto
                    soggetto = self._parse_sog_intestato(key, records)

                    # Aggiungi il soggetto al census
                    census.soggetti.add_soggetto(soggetto)

                except Exception as e:
                    errors.append(f"Errore nel parsing del soggetto {key}: {str(e)}")

            # Solleva un'eccezione se ci sono stati errori nel parsing dei soggetti
            if errors:
                raise ParsingError("Errori nel parsing del file SOG", errors)

            # Se non ci sono soggetti, potrebbe essere un problema
            if not census.soggetti:
                logger.warning("Nessun immobile trovato nel file SOG")

        except ParsingError:
            # Rilanciamo l'eccezione ParsingError senza modificarla
            logger.error("Errori durante il parsing del file SOG")
            raise

        except Exception as e:
            # Per altre eccezioni, le convertiamo in ParsingError
            logger.error(
                f"Errore non previsto durante il parsing del file SOG: {str(e)}"
            )
            raise ParsingError(f"Errore durante il parsing del file SOG: {str(e)}")

    def _parse_sog_record_info(self, line: str) -> SogRecordInfo:
        """
        Estrae le informazioni di base da una riga del file SOG.

        Args:
            line: La riga del file SOG

        Returns:
            SogRecordInfo: Le informazioni estratte

        Raises:
            ValueError: Se la riga è malformata
        """

        try:
            parser = parse_sog_record_info(line=line)
            return parser
        except Exception:
            raise

    def _parse_sog_intestato(self, key: tuple, records: Dict[str, str]) -> Soggetto:
        """
        Crea un oggetto Soggetto dal record estratto.

        Args:
            key: Tupla che identifica il soggetto
            records: Dizionario del record per tipo

        Returns:
            Soggetto: L'oggetto soggetto creato

        Raises:
            ValueError: Se mancano i record obbligatori o se ci sono errori nei record
        """

        # Estrai i dati dalla chiave
        (
            codice_amministrativo,
            sezione,
            identificativo_soggetto,
            tipo_soggetto,
        ) = key

        # Crea i record specifici
        if "P" in records.keys():
            record_p = self._parse_sog_record_p_line(records["P"])
            soggetto = Soggetto(
                codice_amministrativo=codice_amministrativo,
                sezione=sezione,
                identificativo_soggetto=identificativo_soggetto,
                tipo_soggetto=tipo_soggetto,
                record=record_p,
            )
        elif "G" in records.keys():
            record_g = self._parse_sog_record_g_line(records["G"])
            soggetto = Soggetto(
                codice_amministrativo=codice_amministrativo,
                sezione=sezione,
                identificativo_soggetto=identificativo_soggetto,
                tipo_soggetto=tipo_soggetto,
                record=record_g,
            )
        else:
            raise ValueError("Manca il record P o G")

        # Crea e restituisci l'oggetto immobile
        return soggetto

    def _parse_sog_record_p_line(self, line: str) -> SoggettiRecordPrivatePerson:
        """
        Parsifica una riga di record SOG di tipo P.

        Args:
            line: La riga del record

        Returns:
            SoggettiRecordPrivatePerson: L'oggetto record creato

        Raises:
            ValueError: Se la riga è malformata
            ValidationError: Se i dati non rispettano i vincoli del modello
        """

        record_info = parse_sog_record_info(line=line)
        parser = parse_sog_record_p_line(record=record_info)

        return parser

    def _parse_sog_record_g_line(self, line: str) -> SoggettiRecordGiuridicPerson:
        """
        Parsifica una riga di record SOG di tipo G.

        Args:
            line: La riga del record

        Returns:
            SoggettiRecordGiuridicPerson: L'oggetto record creato

        Raises:
            ValueError: Se la riga è malformata
            ValidationError: Se i dati non rispettano i vincoli del modello
        """

        record_info = parse_sog_record_info(line=line)
        parser = parse_sog_record_g_line(record=record_info)

        return parser

    def _parse_tit_file(self, census: Census, content: str) -> None:
        """
        Parsifica un file .TIT e aggiorna l'oggetto Census con i dati delle titolarità.

        Args:
            census: L'oggetto Census da aggiornare
            content: Il contenuto del file TIT

        Raises:
            ValueError: Se il file è vuoto o malformato
            ValidationError: Se i dati non rispettano i vincoli dei modelli
            ParsingError: Se ci sono errori durante il parsing
        """
        if not content:
            raise ValueError("Contenuto del file TIT vuoto o non valido")
        # Inizializza il modello TitolaritaModel se non esiste già
        if not census.titolarita:
            census.titolarita = TitolaritaModel()

        # Errori accumulati durante il parsing
        errors = []

        try:
            # Organizziamo i record per titolarità
            record_groups = {}
            # Processa ogni linea
            for line_num, line in enumerate(content.splitlines(), 1):
                if not line:
                    continue

                try:
                    # Estrai le informazioni di base
                    record_info = self._parse_tit_record_info(line)
                    key = (
                        record_info.codice_amministrativo,
                        record_info.sezione,
                        record_info.identificativo_soggetto,
                        record_info.tipo_soggetto,
                        record_info.identificativo_immobile,
                        record_info.tipo_immobile,
                    )

                    # Se è una nuova titolarità, inizializza il dizionario
                    if key not in record_groups:
                        record_groups[key] = {}

                    # Aggiungi il record al dizionario della titolarità
                    record_groups[key] = record_info.raw_line

                except Exception as e:
                    # Accumula l'errore
                    errors.append(f"Errore alla riga {line_num}: {str(e)}")

            # Solleva un'eccezione se ci sono stati errori durante il parsing delle righe
            if errors:
                print(errors)
                raise ParsingError("Errori nel parsing del file TIT", errors)

            # Processa ogni gruppo di record per creare titolarità
            for key, record_line in record_groups.items():
                try:
                    # Crea la titolarità
                    titolarita = self._parse_tit_record_line(record_line)

                    # Aggiungi la titolarità al census
                    census.titolarita.add_titolarita(titolarita)

                except Exception as e:
                    errors.append(
                        f"Errore nel parsing della titolarità {key}: {str(e)}"
                    )

            # Solleva un'eccezione se ci sono stati errori nel parsing delle titolarità
            if errors:
                raise ParsingError("Errori nel parsing del file TIT", errors)

            # Se non ci sono titolarità, potrebbe essere un problema
            if not census.titolarita.titolarita:
                logger.warning("Nessuna titolarità trovata nel file TIT")

        except ParsingError:
            # Rilanciamo l'eccezione ParsingError senza modificarla
            logger.error("Errori durante il parsing del file TIT")
            raise

        except Exception as e:
            # Per altre eccezioni, le convertiamo in ParsingError
            logger.error(
                f"Errore non previsto durante il parsing del file TIT: {str(e)}"
            )
            raise ParsingError(f"Errore durante il parsing del file TIT: {str(e)}")

    def _parse_tit_record_info(self, line: str) -> TitRecordInfo:
        """
        Estrae le informazioni di base da una riga del file TIT.

        Args:
            line: La riga del file TIT

        Returns:
            TitRecordInfo: Le informazioni estratte

        Raises:
            ValueError: Se la riga è malformata
        """
        try:
            parser = parse_tit_record_info(line=line)
            return parser
        except Exception:
            raise

    def _parse_tit_record_line(self, line: str) -> Titolarita:
        """
        Parsifica una riga di record TIT.

        Args:
            line: La riga del record

        Returns:
            Titolarita: L'oggetto titolarità creato

        Raises:
            ValueError: Se la riga è malformata
            ValidationError: Se i dati non rispettano i vincoli del modello
        """
        record_info = parse_tit_record_info(line=line)
        parser = parse_tit_record_line(record=record_info)
        return parser


def parse_fab_record_info(line: str) -> FabRecordInfo:
    """
    Estrae le informazioni di base da una riga del file FAB.

    Args:
        line: La riga del file FAB

    Returns:
        FabRecordInfo: Le informazioni estratte

    Raises:
        ValueError: Se la riga è malformata
    """

    # Divide la linea nelle parti header e data
    parts = line.split("|")
    if len(parts) < 5:
        raise ValueError(f"Formato riga non valido: {line}")

    header = parts[:6]
    data = parts[6:]

    # Estrai i campi chiave dall'header
    if len(header) < 5:
        raise ValueError(f"Header troppo corto: {header}")

    codice_amministrativo = header[0]
    sezione = header[1]
    identificativo_immobile = header[2]
    tipo_immobile = header[3]
    progressivo = header[4]
    tipo_record = header[5]

    # Crea e restituisci l'oggetto FabRecordInfo
    try:
        return FabRecordInfo(
            codice_amministrativo=codice_amministrativo,
            sezione=sezione,
            identificativo_immobile=identificativo_immobile,
            tipo_immobile=tipo_immobile,
            progressivo=progressivo,
            tipo_record=tipo_record,
            data=data,  # La parte dati dopo il tipo record
            raw_line=line,  # Linea completa per riferimento
            raw_tuple=parts,  # non tiene in considerazione la specifica
            items_number=len(
                parts
            ),  # La lunghezza non tiene in considerazione la specifica
        )
    except ValidationError:
        raise


def parse_fab_record1_line(
    record: FabRecordInfo,
) -> FabbricatiRecord1:
    """
    Parsifica una riga di record di tipo 1.

    Args:
        record: La riga del record con modello FabRecordInfo

    Returns:
        FabbricatiRecord1: L'oggetto record creato

    Raises:
        ValidationError: Se i dati non rispettano i vincoli del modello
    """

    # Crea un dizionario con i campi di base
    record_data = {
        "codice_amministrativo": record.codice_amministrativo,
        "sezione": record.sezione,
        "identificativo_immobile": record.identificativo_immobile,
        "tipo_immobile": record.tipo_immobile,
        "progressivo": record.progressivo,
        "tipo_record": record.tipo_record,
    }

    # Mappa dei campi in base alla posizione nei dati suddivisi

    field_mapping = [
        "zona",
        "categoria",
        "classe",
        "consistenza",
        "superficie",
        "rendita_lire",
        "rendita_euro",
        "lotto",
        "edificio",
        "scala",
        "interno1",
        "interno2",
        "piano1",
        "piano2",
        "piano3",
        "piano4",
        "data_efficacia_iniziale",
        "data_registrazione_atti_iniziale",
        "tipo_nota_iniziale",
        "numero_nota_iniziale",
        "progressivo_nota_iniziale",
        "anno_nota_iniziale",
        "data_efficacia_finale",
        "data_registrazione_atti_finale",
        "tipo_nota_finale",
        "numero_nota_finale",
        "progressivo_nota_finale",
        "anno_nota_finale",
        "partita",
        "annotazione",
        "identificativo_mutazione_iniziale",
        "identificativo_mutazione_finale",
        "protocollo_notifica",
        "data_notifica",
        "codice_causale_atto_generante",
        "descrizione_atto_generante",
        "codice_causale_atto_conclusivo",
        "descrizione_atto_conclusivo",
        "flag_classamento",
    ]

    # Popola il dizionario con i valori dai campi
    if len(record.data) % len(field_mapping) > 0:
        record.data = record.data[
            : len(record.data) - (len(record.data) % len(field_mapping))
        ]  # elimino l'ultimo elemento non rilevante
    for i, field_name in enumerate(field_mapping):
        if i <= len(record.data):
            record_data[field_name] = record.data[i]

    # Validazione con Pydantic: questo solleverà ValidationError se i dati non rispettano i vincoli
    try:
        record1 = FabbricatiRecord1(**record_data)
    except ValidationError:
        raise

    return record1


def parse_fab_record2_line(
    record: FabRecordInfo,
) -> FabbricatiRecord2:
    """
    Parsifica una riga di record di tipo 2.

    Args:
        record: La riga del record con modello FabRecordInfo

    Returns:
        FabbricatiRecord2: L'oggetto record creato

    Raises:
        ValidationError: Se i dati non rispettano i vincoli del modello
    """

    # Crea un dizionario con i campi di base
    record_data = {
        "codice_amministrativo": record.codice_amministrativo,
        "sezione": record.sezione,
        "identificativo_immobile": record.identificativo_immobile,
        "tipo_immobile": record.tipo_immobile,
        "progressivo": record.progressivo,
        "tipo_record": record.tipo_record,
    }

    # Mappa dei campi in base alla posizione nei dati suddivisi

    field_mapping = [
        "sezione_urbana",
        "foglio",
        "numero",
        "denominatore",
        "subalterno",
        "edificialita",
    ]

    # Lista per contenere tutti gli identificativi
    num_identificativi = len(record.data) // len(field_mapping)
    identificativi = []

    # Itera attraverso i blocchi di dati per creare ogni identificativo
    for i in range(num_identificativi):
        # Estrai i dati per questo identificativo
        start_idx = i * len(field_mapping)
        end_idx = start_idx + len(field_mapping)

        # Se non ci sono abbastanza dati, interrompi il ciclo
        if start_idx >= len(record.data):
            break

        # Estrai i dati per questo identificativo
        id_data = record.data[start_idx:end_idx]

        # Crea un dizionario per questo identificativo
        identificativo_data = {}
        for j, field_name in enumerate(field_mapping):
            if j <= len(id_data):
                identificativo_data[field_name] = id_data[j]

        # Crea l'oggetto Identificativo e aggiungilo alla lista
        try:
            identificativo = Identificativo(**identificativo_data)
            identificativi.append(identificativo)
        except ValidationError as e:
            print(f"Errore nella creazione dell'identificativo {i+1}: {str(e)}")
            raise

    # Aggiungi la lista di identificativi al dizionario dei dati del record
    record_data["identificativi"] = identificativi

    # Crea e restituisci l'oggetto FabbricatiRecord2
    try:
        return FabbricatiRecord2(**record_data)
    except ValidationError as e:
        print(f"Errore nella creazione del record2: {str(e)}")
        raise


def parse_fab_record3_line(
    record: FabRecordInfo,
) -> FabbricatiRecord3:
    """
    Parsifica una riga di record di tipo 3.

    Args:
        record: La riga del record con modello FabRecordInfo

    Returns:
        FabbricatiRecord2: L'oggetto record creato

    Raises:
        ValidationError: Se i dati non rispettano i vincoli del modello
    """

    # Crea un dizionario con i campi di base
    record_data = {
        "codice_amministrativo": record.codice_amministrativo,
        "sezione": record.sezione,
        "identificativo_immobile": record.identificativo_immobile,
        "tipo_immobile": record.tipo_immobile,
        "progressivo": record.progressivo,
        "tipo_record": record.tipo_record,
    }

    # Mappa dei campi in base alla posizione nei dati suddivisi

    field_mapping = [
        "toponimo",
        "indirizzo",
        "civico1",
        "civico2",
        "civico3",
        "codice_strada",
    ]

    # Lista per contenere tutti gli identificativi
    num_indirizzi = len(record.data) // len(field_mapping)
    indirizzi = []

    # Itera attraverso i blocchi di dati per creare ogni identificativo
    for i in range(num_indirizzi):
        # Estrai i dati per questo identificativo
        start_idx = i * len(field_mapping)
        end_idx = start_idx + len(field_mapping)

        # Se non ci sono abbastanza dati, interrompi il ciclo
        if start_idx >= len(record.data):
            break

        # Estrai i dati per questo identificativo
        id_data = record.data[start_idx:end_idx]

        # Crea un dizionario per questo identificativo
        indirizzo_data = {}
        for j, field_name in enumerate(field_mapping):
            if j <= len(id_data):
                indirizzo_data[field_name] = id_data[j]

        # Crea l'oggetto Indirizzo e aggiungilo alla lista
        try:
            indirizzo = Indirizzo(**indirizzo_data)
            indirizzi.append(indirizzo)
        except ValidationError as e:
            print(f"Errore nella creazione dell'indirizzo {i+1}: {str(e)}")
            raise

    # Aggiungi la lista di indirizzi al dizionario dei dati del record
    record_data["indirizzi"] = indirizzi

    # Crea e restituisci l'oggetto FabbricatiRecord3
    try:
        return FabbricatiRecord3(**record_data)
    except ValidationError as e:
        print(f"Errore nella creazione del record3: {str(e)}")
        raise


def parse_fab_record4_line(
    record: FabRecordInfo,
) -> FabbricatiRecord4:
    """
    Parsifica una riga di record di tipo 4.

    Args:
        record: La riga del record con modello FabRecordInfo

    Returns:
        FabbricatiRecord2: L'oggetto record creato

    Raises:
        ValidationError: Se i dati non rispettano i vincoli del modello
    """

    # Crea un dizionario con i campi di base
    record_data = {
        "codice_amministrativo": record.codice_amministrativo,
        "sezione": record.sezione,
        "identificativo_immobile": record.identificativo_immobile,
        "tipo_immobile": record.tipo_immobile,
        "progressivo": record.progressivo,
        "tipo_record": record.tipo_record,
    }

    # Mappa dei campi in base alla posizione nei dati suddivisi

    field_mapping = [
        "sezione_urbana",
        "foglio",
        "numero",
        "denominatore",
        "subalterno",
    ]

    # Lista per contenere tutti gli identificativi
    num_utilita_comune = len(record.data) // len(field_mapping)
    utilita_comuni = []

    # Itera attraverso i blocchi di dati per creare ogni identificativo
    for i in range(num_utilita_comune):
        # Estrai i dati per questo identificativo
        start_idx = i * len(field_mapping)
        end_idx = start_idx + len(field_mapping)

        # Se non ci sono abbastanza dati, interrompi il ciclo
        if start_idx >= len(record.data):
            break

        # Estrai i dati per questo identificativo
        id_data = record.data[start_idx:end_idx]

        # Crea un dizionario per questo identificativo
        utilita_comune_data = {}
        for j, field_name in enumerate(field_mapping):
            if j <= len(id_data):
                utilita_comune_data[field_name] = id_data[j]

        # Crea l'oggetto Indirizzo e aggiungilo alla lista
        try:
            utilita_comune = UtilitaComune(**utilita_comune_data)
            utilita_comuni.append(utilita_comune)
        except ValidationError as e:
            print(f"Errore nella creazione dell'utilita comune {i+1}: {str(e)}")
            raise

    # Aggiungi la lista di utilita_comuni al dizionario dei dati del record
    record_data["utilita_comuni"] = utilita_comuni

    # Crea e restituisci l'oggetto FabbricatiRecord3
    try:
        return FabbricatiRecord4(**record_data)
    except ValidationError as e:
        print(f"Errore nella creazione del record4: {str(e)}")
        raise


def parse_fab_record5_line(
    record: FabRecordInfo,
) -> FabbricatiRecord5:
    """
    Parsifica una riga di record di tipo 5.

    Args:
        record: La riga del record con modello FabRecordInfo

    Returns:
        FabbricatiRecord2: L'oggetto record creato

    Raises:
        ValidationError: Se i dati non rispettano i vincoli del modello
    """

    # Crea un dizionario con i campi di base
    record_data = {
        "codice_amministrativo": record.codice_amministrativo,
        "sezione": record.sezione,
        "identificativo_immobile": record.identificativo_immobile,
        "tipo_immobile": record.tipo_immobile,
        "progressivo": record.progressivo,
        "tipo_record": record.tipo_record,
    }

    # Mappa dei campi in base alla posizione nei dati suddivisi

    field_mapping = [
        "codice_riserva",
        "partita_iscrizione_riserva",
    ]

    # Lista per contenere tutti gli identificativi
    num_riserva = len(record.data) // len(field_mapping)
    riserve = []

    # Itera attraverso i blocchi di dati per creare ogni riserva
    for i in range(num_riserva):
        # Estrai i dati per questa riserva
        start_idx = i * len(field_mapping)
        end_idx = start_idx + len(field_mapping)

        # Se non ci sono abbastanza dati, interrompi il ciclo
        if start_idx >= len(record.data):
            break

        # Estrai i dati per questa riserva
        id_data = record.data[start_idx:end_idx]

        # Crea un dizionario per questo riserva
        riserva_data = {}
        for j, field_name in enumerate(field_mapping):
            if j <= len(id_data):
                riserva_data[field_name] = id_data[j]

        # Crea l'oggetto Riserva e aggiungilo alla lista
        try:
            riserva = BuildingRiserva(**riserva_data)
            riserve.append(riserva)
        except ValidationError as e:
            print(f"Errore nella creazione della riserva {i+1}: {str(e)}")
            raise

    # Aggiungi la lista di riserve al dizionario dei dati del record
    record_data["riserve"] = riserve

    # Crea e restituisci l'oggetto FabbricatiRecord5
    try:
        return FabbricatiRecord5(**record_data)
    except ValidationError as e:
        print(f"Errore nella creazione del record4: {str(e)}")
        raise


def parse_ter_record_info(line: str) -> TerRecordInfo:
    """
    Estrae le informazioni di base da una riga del file TER.

    Args:
        line: La riga del file TER

    Returns:
        TerRecordInfo: Le informazioni estratte

    Raises:
        ValueError: Se la riga è malformata
    """

    # Divide la linea nelle parti header e data
    parts = line.split("|")
    if len(parts) < 5:
        raise ValueError(f"Formato riga non valido: {line}")

    header = parts[:6]
    data = parts[6:]

    # Estrai i campi chiave dall'header
    if len(header) < 5:
        raise ValueError(f"Header troppo corto: {header}")

    codice_amministrativo = header[0]
    sezione = header[1]
    identificativo_immobile = header[2]
    tipo_immobile = header[3]
    progressivo = header[4]
    tipo_record = header[5]

    # Crea e restituisci l'oggetto TerRecordInfo
    try:
        return TerRecordInfo(
            codice_amministrativo=codice_amministrativo,
            sezione=sezione,
            identificativo_immobile=identificativo_immobile,
            tipo_immobile=tipo_immobile,
            progressivo=progressivo,
            tipo_record=tipo_record,
            data=data,  # La parte dati dopo il tipo record
            raw_line=line,  # Linea completa per riferimento
            raw_tuple=parts,  # non tiene in considerazione la specifica
            items_number=len(
                parts
            ),  # La lunghezza non tiene in considerazione la specifica
        )
    except ValidationError:
        raise


def parse_ter_record1_line(
    record: TerRecordInfo,
) -> TerreniRecord1:
    """
    Parsifica una riga di record di tipo 1.

    Args:
        record: La riga del record con modello TerRecordInfo

    Returns:
        TerreniRecord1: L'oggetto record creato

    Raises:
        ValidationError: Se i dati non rispettano i vincoli del modello
    """

    # Crea un dizionario con i campi di base
    record_data = {
        "codice_amministrativo": record.codice_amministrativo,
        "sezione": record.sezione,
        "identificativo_immobile": record.identificativo_immobile,
        "tipo_immobile": record.tipo_immobile,
        "progressivo": record.progressivo,
        "tipo_record": record.tipo_record,
    }

    # Mappa dei campi in base alla posizione nei dati suddivisi

    field_mapping = [
        "foglio",
        "numero",
        "denominatore",
        "subalterno",
        "edificialita",
        "qualita",
        "classe",
        "ettari",
        "are",
        "centiare",
        "flag_reddito",
        "flag_porzione",
        "flag_deduzioni",
        "reddito_dominicale_lire",
        "reddito_agrario_lire",
        "reddito_dominicale_euro",
        "reddito_agrario_euro",
        "data_efficacia_iniziale",
        "data_registrazione_atti_iniziale",
        "tipo_nota_iniziale",
        "numero_nota_iniziale",
        "progressivo_nota_iniziale",
        "anno_nota_iniziale",
        "data_efficacia_finale",
        "data_registrazione_atti_finale",
        "tipo_nota_finale",
        "numero_nota_finale",
        "progressivo_nota_finale",
        "anno_nota_finale",
        "partita",
        "annotazione",
        "identificativo_mutazione_iniziale",
        "identificativo_mutazione_finale",
        "codice_causale_atto_generante",
        "descrizione_atto_generante",
        "codice_causale_atto_conclusivo",
        "descrizione_atto_conclusivo",
    ]

    # Popola il dizionario con i valori dai campi
    if len(record.data) % len(field_mapping) > 0:
        record.data = record.data[
            : len(record.data) - (len(record.data) % len(field_mapping))
        ]  # elimino l'ultimo elemento non rilevante
    for i, field_name in enumerate(field_mapping):
        if i <= len(record.data):
            record_data[field_name] = record.data[i]

    # Validazione con Pydantic: questo solleverà ValidationError se i dati non rispettano i vincoli
    try:
        record1 = TerreniRecord1(**record_data)
    except ValidationError:
        raise

    return record1


def parse_ter_record2_line(
    record: TerRecordInfo,
) -> TerreniRecord2:
    """
    Parsifica una riga di record di tipo 2.

    Args:
        record: La riga del record con modello TerRecordInfo

    Returns:
        TerreniRecord2: L'oggetto record creato

    Raises:
        ValidationError: Se i dati non rispettano i vincoli del modello
    """

    # Crea un dizionario con i campi di base
    record_data = {
        "codice_amministrativo": record.codice_amministrativo,
        "sezione": record.sezione,
        "identificativo_immobile": record.identificativo_immobile,
        "tipo_immobile": record.tipo_immobile,
        "progressivo": record.progressivo,
        "tipo_record": record.tipo_record,
    }

    # Mappa dei campi in base alla posizione nei dati suddivisi

    field_mapping = [
        "simbolo_deduzione",
    ]

    # Lista per contenere tutti le deduzioni
    num_deduzioni = len(record.data) // len(field_mapping)
    deduzioni = []

    # Itera attraverso i blocchi di dati per creare ogni deduzione
    for i in range(num_deduzioni):
        # Estrai i dati per questo deduzione
        start_idx = i * len(field_mapping)
        end_idx = start_idx + len(field_mapping)

        # Se non ci sono abbastanza dati, interrompi il ciclo
        if start_idx >= len(record.data):
            break

        # Estrai i dati per questo deduzione
        id_data = record.data[start_idx:end_idx]

        # Crea un dizionario per questo deduzione
        deduzione_data = {}
        for j, field_name in enumerate(field_mapping):
            if j <= len(id_data):
                deduzione_data[field_name] = id_data[j]

        # Crea l'oggetto Deduzione e aggiungilo alla lista
        try:
            deduzione = Deduzione(**deduzione_data)
            deduzioni.append(deduzione)
        except ValidationError as e:
            print(f"Errore nella creazione della deduzione {i+1}: {str(e)}")
            raise

    # Aggiungi la lista di deduzioni al dizionario dei dati del record
    record_data["deduzioni"] = deduzioni

    # Crea e restituisci l'oggetto TerreniRecord2
    try:
        return TerreniRecord2(**record_data)
    except ValidationError as e:
        print(f"Errore nella creazione del record2: {str(e)}")
        raise


def parse_ter_record3_line(
    record: TerRecordInfo,
) -> TerreniRecord3:
    """
    Parsifica una riga di record di tipo 3.

    Args:
        record: La riga del record con modello FabRecordInfo

    Returns:
        TerreniRecord3: L'oggetto record creato

    Raises:
        ValidationError: Se i dati non rispettano i vincoli del modello
    """

    # Crea un dizionario con i campi di base
    record_data = {
        "codice_amministrativo": record.codice_amministrativo,
        "sezione": record.sezione,
        "identificativo_immobile": record.identificativo_immobile,
        "tipo_immobile": record.tipo_immobile,
        "progressivo": record.progressivo,
        "tipo_record": record.tipo_record,
    }

    # Mappa dei campi in base alla posizione nei dati suddivisi

    field_mapping = [
        "codice_riserva",
        "partita_iscrizione_riserva",
    ]

    # Lista per contenere tutti gli riserve
    num_riserve = len(record.data) // len(field_mapping)
    riserve = []

    # Itera attraverso i blocchi di dati per creare ogni riserva
    for i in range(num_riserve):
        # Estrai i dati per questa riserva
        start_idx = i * len(field_mapping)
        end_idx = start_idx + len(field_mapping)

        # Se non ci sono abbastanza dati, interrompi il ciclo
        if start_idx >= len(record.data):
            break

        # Estrai i dati per questa riserva
        id_data = record.data[start_idx:end_idx]

        # Crea un dizionario per questo riserva
        riserva_data = {}
        for j, field_name in enumerate(field_mapping):
            if j <= len(id_data):
                riserva_data[field_name] = id_data[j]

        # Crea l'oggetto Riserva e aggiungilo alla lista
        try:
            riserva = LandRiserva(**riserva_data)
            riserve.append(riserva)
        except ValidationError as e:
            print(f"Errore nella creazione della riserva {i+1}: {str(e)}")
            raise

    # Aggiungi la lista di riserve al dizionario dei dati del record
    record_data["riserve"] = riserve

    # Crea e restituisci l'oggetto TerreniRecord3
    try:
        return TerreniRecord3(**record_data)
    except ValidationError as e:
        print(f"Errore nella creazione del record3: {str(e)}")
        raise


def parse_ter_record4_line(
    record: TerRecordInfo,
) -> TerreniRecord4:
    """
    Parsifica una riga di record di tipo 4.

    Args:
        record: La riga del record con modello TerRecordInfo

    Returns:
        TerreniRecord4: L'oggetto record creato

    Raises:
        ValidationError: Se i dati non rispettano i vincoli del modello
    """

    # Crea un dizionario con i campi di base
    record_data = {
        "codice_amministrativo": record.codice_amministrativo,
        "sezione": record.sezione,
        "identificativo_immobile": record.identificativo_immobile,
        "tipo_immobile": record.tipo_immobile,
        "progressivo": record.progressivo,
        "tipo_record": record.tipo_record,
    }

    # Mappa dei campi in base alla posizione nei dati suddivisi

    field_mapping = [
        "identificativo_porzione",
        "qualita",
        "classe",
        "ettari",
        "are",
        "centiare",
        "reddito_dominicale_euro",
        "reddito_agrario_euro",
    ]

    # Lista per contenere tutte le porzioni
    num_porzioni = len(record.data) // len(field_mapping)
    porzioni = []

    # Itera attraverso i blocchi di dati per creare ogni porzione
    for i in range(num_porzioni):
        # Estrai i dati per questo porzione
        start_idx = i * len(field_mapping)
        end_idx = start_idx + len(field_mapping)

        # Se non ci sono abbastanza dati, interrompi il ciclo
        if start_idx >= len(record.data):
            break

        # Estrai i dati per questo identificativo
        id_data = record.data[start_idx:end_idx]

        # Crea un dizionario per questo identificativo
        porzione_data = {}
        for j, field_name in enumerate(field_mapping):
            if j <= len(id_data):
                porzione_data[field_name] = id_data[j]

        # Crea l'oggetto PorzioneSdi e aggiungilo alla lista
        try:
            porzione = PorzioneSdi(**porzione_data)
            porzioni.append(porzione)
        except ValidationError as e:
            print(f"Errore nella creazione della porzione {i+1}: {str(e)}")
            raise

    # Aggiungi la lista di porzioni al dizionario dei dati del record
    record_data["porzioni"] = porzioni

    # Crea e restituisci l'oggetto TerreniRecord4
    try:
        return TerreniRecord4(**record_data)
    except ValidationError as e:
        print(f"Errore nella creazione del record4: {str(e)}")
        raise


def parse_sog_record_info(line: str) -> SogRecordInfo:
    """
    Estrae le informazioni di base da una riga del file SOG.

    Args:
        line: La riga del file SOG

    Returns:
        SogRecordInfo: Le informazioni estratte

    Raises:
        ValueError: Se la riga è malformata
    """

    # Divide la linea nelle parti header e data
    parts = line.split("|")
    if len(parts) < 4:
        raise ValueError(f"Formato riga non valido: {line}")

    header = parts[:4]
    data = parts[4:]

    # Estrai i campi chiave dall'header
    if len(header) < 4:
        raise ValueError(f"Header troppo corto: {header}")

    codice_amministrativo = header[0]
    sezione = header[1]
    identificativo_soggetto = header[2]
    tipo_soggetto = header[3]

    # Crea e restituisci l'oggetto FabRecordInfo
    try:
        return SogRecordInfo(
            codice_amministrativo=codice_amministrativo,
            sezione=sezione,
            identificativo_soggetto=identificativo_soggetto,
            tipo_soggetto=tipo_soggetto,
            data=data,  # La parte dati dopo il tipo record
            raw_line=line,  # Linea completa per riferimento
            raw_tuple=parts,  # non tiene in considerazione la specifica
            items_number=len(
                parts
            ),  # La lunghezza non tiene in considerazione la specifica
        )
    except ValidationError:
        raise


def parse_sog_record_p_line(
    record: SogRecordInfo,
) -> SoggettiRecordPrivatePerson:
    """
    Parsifica una riga di record SOG di tipo P.

    Args:
        record: La riga del record con modello SogRecordInfo

    Returns:
        SoggettiRecordPrivatePerson: L'oggetto record creato

    Raises:
        ValidationError: Se i dati non rispettano i vincoli del modello
    """

    # Crea un dizionario con i campi di base
    record_data = {
        "codice_amministrativo": record.codice_amministrativo,
        "sezione": record.sezione,
        "identificativo_soggetto": record.identificativo_soggetto,
        "tipo_soggetto": record.tipo_soggetto,
    }

    # Mappa dei campi in base alla posizione nei dati suddivisi

    field_mapping = [
        "cognome",
        "nome",
        "sesso",
        "data_di_nascita",
        "luogo_di_nascita",
        "codice_fiscale",
        "indicazioni_supplementari",
    ]

    # Popola il dizionario con i valori dai campi
    if len(record.data) % len(field_mapping) > 0:
        record.data = record.data[
            : len(record.data) - (len(record.data) % len(field_mapping))
        ]  # elimino l'ultimo elemento non rilevante
    for i, field_name in enumerate(field_mapping):
        if i <= len(record.data):
            record_data[field_name] = record.data[i]

    # Validazione con Pydantic: questo solleverà ValidationError se i dati non rispettano i vincoli
    try:
        record_p = SoggettiRecordPrivatePerson(**record_data)
    except ValidationError:
        raise

    return record_p


def parse_sog_record_g_line(
    record: SogRecordInfo,
) -> SoggettiRecordGiuridicPerson:
    """
    Parsifica una riga di record SOG di tipo G.

    Args:
        record: La riga del record con modello SogRecordInfo

    Returns:
        SoggettiRecordGiuridicPerson: L'oggetto record creato

    Raises:
        ValidationError: Se i dati non rispettano i vincoli del modello
    """

    # Crea un dizionario con i campi di base
    record_data = {
        "codice_amministrativo": record.codice_amministrativo,
        "sezione": record.sezione,
        "identificativo_soggetto": record.identificativo_soggetto,
        "tipo_soggetto": record.tipo_soggetto,
    }

    # Mappa dei campi in base alla posizione nei dati suddivisi

    field_mapping = [
        "denominazione",
        "sede",
        "codice_fiscale",
    ]

    # Popola il dizionario con i valori dai campi
    if len(record.data) % len(field_mapping) > 0:
        record.data = record.data[
            : len(record.data) - (len(record.data) % len(field_mapping))
        ]  # elimino l'ultimo elemento non rilevante
    for i, field_name in enumerate(field_mapping):
        if i <= len(record.data):
            record_data[field_name] = record.data[i]

    # Validazione con Pydantic: questo solleverà ValidationError se i dati non rispettano i vincoli
    try:
        record_g = SoggettiRecordGiuridicPerson(**record_data)
    except ValidationError:
        raise

    return record_g


def parse_tit_record_info(line: str) -> TitRecordInfo:
    """
    Estrae le informazioni di base da una riga del file TIT.

    Args:
        line: La riga del file TIT

    Returns:
        TitRecordInfo: Le informazioni estratte

    Raises:
        ValueError: Se la riga è malformata
    """
    # Divide la linea nelle parti header e data
    parts = line.split("|")
    if len(parts) < 6:
        raise ValueError(f"Formato riga non valido: {line}")

    header = parts[:6]
    data = parts[6:]

    # Estrai i campi chiave dall'header
    if len(header) < 6:
        raise ValueError(f"Header troppo corto: {header}")

    codice_amministrativo = header[0]
    sezione = header[1]
    identificativo_soggetto = header[2]
    tipo_soggetto = header[3]
    identificativo_immobile = header[4]
    tipo_immobile = header[5]

    # Crea e restituisci l'oggetto TitRecordInfo
    try:
        return TitRecordInfo(
            codice_amministrativo=codice_amministrativo,
            sezione=sezione,
            identificativo_soggetto=identificativo_soggetto,
            tipo_soggetto=tipo_soggetto,
            identificativo_immobile=identificativo_immobile,
            tipo_immobile=tipo_immobile,
            data=data,  # La parte dati dopo i campi base
            raw_line=line,  # Linea completa per riferimento
            raw_tuple=parts,  # Tupla completa degli elementi
            items_number=len(parts),  # Numero elementi nel record
        )
    except ValidationError:
        raise


def parse_tit_record_line(record: TitRecordInfo) -> Titolarita:
    """
    Parsifica una riga di record TIT.

    Args:
        record: Le informazioni di base del record

    Returns:
        Titolarita: L'oggetto titolarità creato

    Raises:
        ValidationError: Se i dati non rispettano i vincoli del modello
    """
    # Crea un dizionario con i campi di base
    record_data = {
        "codice_amministrativo": record.codice_amministrativo,
        "sezione": record.sezione,
        "identificativo_soggetto": record.identificativo_soggetto,
        "tipo_soggetto": record.tipo_soggetto,
        "identificativo_immobile": record.identificativo_immobile,
        "tipo_immobile": record.tipo_immobile,
    }

    # Mappa dei campi in base alla posizione nei dati suddivisi
    field_mapping = [
        "codice_diritto",
        "titolo_non_codificato",
        "quota_numeratore",
        "quota_denominatore",
        "regime",
        "soggetto_di_riferimento",
        "data_di_validita_iniziale",
        "tipo_nota_iniziale",
        "numero_nota_iniziale",
        "progressivo_nota_iniziale",
        "anno_nota_iniziale",
        "data_registrazione_atti_iniziale",
        "partita",
        "data_di_validita_finale",
        "tipo_nota_finale",
        "numero_nota_finale",
        "progressivo_nota_finale",
        "anno_nota_finale",
        "data_registrazione_atti_finale",
        "identificativo_mutazione_iniziale",
        "identificativo_mutazione_finale",
        "identificativo_titolarita",
        "codice_causale_atto_generante",
        "descrizione_atto_generante",
        "codice_causale_atto_conclusivo",
        "descrizione_atto_conclusivo",
    ]

    # Popola il dizionario con i valori dai campi
    for i, field_name in enumerate(field_mapping):
        if i < len(record.data):
            # Converti i campi per enum
            if field_name == "tipo_soggetto":
                record_data[field_name] = TipoSoggettoEnum(record.data[i])
            elif field_name == "tipo_immobile":
                record_data[field_name] = TipoImmobileEnum(record.data[i])
            elif field_name == "regime" and record.data[i]:
                record_data[field_name] = TipoRegimeEnum(record.data[i])
            else:
                record_data[field_name] = record.data[i]

    # Validazione con Pydantic: questo solleverà ValidationError se i dati non rispettano i vincoli
    try:
        record_tit = Titolarita(**record_data)
    except ValidationError:
        raise

    return record_tit
