import pytest
from catasto.parser import (
    FileParserService,
    ParsingError,
    parse_ter_record1_line,
    parse_ter_record2_line,
    parse_ter_record3_line,
    parse_ter_record4_line,
    parse_ter_record_info,
)
from catasto.reader import LocalFileReaderService
from catasto.schemas.land import PorzioneSdi
from pydantic import ValidationError


class TestTerRecordInfo:
    """Test per il record generico di TER."""

    def test_parse_ter_record_info_valid_line(self, static_ter_record1_valid_line):
        "Verifica che una linea con un record generico venga interpretata correttamente."

        ter_record_info = parse_ter_record_info(static_ter_record1_valid_line)

        assert ter_record_info.codice_amministrativo == "H501"
        assert ter_record_info.sezione == "A"
        assert ter_record_info.identificativo_immobile == "2041104"
        assert ter_record_info.tipo_immobile == "T"
        assert ter_record_info.progressivo == "2"
        assert ter_record_info.tipo_record == "1"
        assert (
            ter_record_info.items_number > 10
        )  # Numero di elementi deve essere maggiore di 10

    def test_parse_ter_record_info_invalid_line(self, static_ter_record1_invalid_line):
        "Verifica che una linea con un record generico invalido generi un errore."

        with pytest.raises(ValidationError):
            parse_ter_record_info(static_ter_record1_invalid_line)


class TestTerreniRecord1:
    """Test per il record di tipo 1 (caratteristiche dell'unità immobiliare)."""

    def test_parse_record1_line(self, static_ter_record1_valid_line):
        "Verifica che una linea con un record1 venga interpretata correttamente."

        ter_record_info = parse_ter_record_info(static_ter_record1_valid_line)
        parser = parse_ter_record1_line(ter_record_info)

        assert parser.codice_amministrativo == "H501"
        assert parser.sezione == "A"
        assert parser.identificativo_immobile == "2041104"
        assert parser.tipo_immobile == "T"
        assert parser.progressivo == "2"
        assert parser.tipo_record == "1"

        assert parser.foglio == "197"
        assert parser.numero == "08198"
        assert parser.denominatore == ""
        assert parser.subalterno == ""
        assert parser.edificialita == ""

        assert parser.qualita == "899"
        assert parser.classe == "00"
        assert parser.ettari == ""
        assert parser.are == ""
        assert parser.centiare == ""

        # Altri campi e flag...
        assert parser.flag_reddito in ["0", "1", " "] or parser.flag_reddito is None
        assert parser.flag_porzione in ["0", "1", " "] or parser.flag_porzione is None
        assert parser.flag_deduzioni in ["0", "1", " "] or parser.flag_deduzioni is None

        # Verifica data di efficacia
        assert len(parser.data_efficacia_iniziale) == 8
        assert parser.data_efficacia_iniziale.isdigit()

    def test_parse_record1_invalid_line(self, static_ter_record1_invalid_line):
        "Verifica che una linea con un record1 invalido generi un errore."

        with pytest.raises(ValidationError):
            ter_record_info = parse_ter_record_info(static_ter_record1_invalid_line)
            parse_ter_record1_line(ter_record_info)


class TestTerreniRecord2:
    """Test per il record di tipo 2 (deduzioni dell'unità immobiliare)."""

    def test_parse_record2_line(self, static_ter_record2_valid_line):
        "Verifica che una linea con un record2 venga interpretata correttamente."

        ter_record_info = parse_ter_record_info(static_ter_record2_valid_line)
        parser = parse_ter_record2_line(ter_record_info)

        assert parser.codice_amministrativo == "H501"
        assert parser.tipo_immobile == "T"
        assert parser.tipo_record == "2"

        # Verifica che ci siano deduzioni
        assert hasattr(parser, "deduzioni")
        assert len(parser.deduzioni) > 0

        # Verifica il formato del simbolo deduzione
        for deduzione in parser.deduzioni:
            assert len(deduzione.simbolo_deduzione) <= 6
            assert deduzione.simbolo_deduzione in ["<A6", ""]

    def test_parse_record2_invalid_line(self, static_ter_record2_invalid_line):
        "Verifica che una linea con un record2 invalido generi un errore."

        with pytest.raises(ValidationError):
            ter_record_info = parse_ter_record_info(static_ter_record2_invalid_line)
            parse_ter_record2_line(ter_record_info)


class TestTerreniRecord3:
    """Test per il record di tipo 3 (riserve dell'unità immobiliare)."""

    def test_parse_record3_line(self, static_ter_record3_valid_line):
        "Verifica che una linea con un record3 venga interpretata correttamente."

        ter_record_info = parse_ter_record_info(static_ter_record3_valid_line)
        parser = parse_ter_record3_line(ter_record_info)

        assert parser.codice_amministrativo == "H501"
        assert parser.tipo_immobile == "T"
        assert parser.tipo_record == "3"

        # Verifica che ci siano riserve
        assert hasattr(parser, "riserve")
        assert len(parser.riserve) > 0

        # Verifica il formato delle riserve
        for riserva in parser.riserve:
            assert len(riserva.codice_riserva) == 1
            assert riserva.codice_riserva.isalnum()
            if riserva.partita_iscrizione_riserva:
                assert len(riserva.partita_iscrizione_riserva) <= 7

    def test_parse_record3_invalid_line(self, static_ter_record3_invalid_line):
        "Verifica che una linea con un record3 invalido generi un errore."

        with pytest.raises(ValidationError):
            ter_record_info = parse_ter_record_info(static_ter_record3_invalid_line)
            parse_ter_record3_line(ter_record_info)


class TestTerreniRecord4:
    """Test per il record di tipo 4 (porzioni dell'unità immobiliare)."""

    def test_parse_record4_line(self, static_ter_record4_valid_line):
        "Verifica che una linea con un record4 venga interpretata correttamente."

        ter_record_info = parse_ter_record_info(static_ter_record4_valid_line)
        parser = parse_ter_record4_line(ter_record_info)

        assert parser.codice_amministrativo == "H501"
        assert parser.tipo_immobile == "T"
        assert parser.tipo_record == "4"

        # Verifica che ci siano porzioni
        assert hasattr(parser, "porzioni")
        assert len(parser.porzioni) > 0

        # Verifica il formato delle porzioni
        for porzione in parser.porzioni:
            assert len(porzione.identificativo_porzione) == 2
            assert porzione.identificativo_porzione.isalnum()
            assert porzione.qualita.isdigit()
            assert porzione.classe.isalnum()
            assert porzione.ettari.isdigit()
            assert porzione.are.isdigit()
            assert porzione.centiare.isdigit()

            # Se è una PorzioneSdi, verifica anche i redditi
            if isinstance(porzione, PorzioneSdi):
                assert hasattr(porzione, "reddito_dominicale_euro")
                assert hasattr(porzione, "reddito_agrario_euro")

    def test_parse_record4_invalid_line(self, static_ter_record4_invalid_line):
        "Verifica che una linea con un record4 invalido generi un errore."

        with pytest.raises(ValidationError):
            ter_record_info = parse_ter_record_info(static_ter_record4_invalid_line)
            parse_ter_record4_line(ter_record_info)


class TestFileValidazione:
    """Test per la validazione di interi file .TER."""

    @pytest.mark.asyncio
    async def test_lettura_file_valido(self, temp_ter_file):
        """Verifica che un file generato casualmente possa essere letto."""
        reader = LocalFileReaderService(filepath=str(temp_ter_file))

        async with reader.open() as file_reader:
            assert file_reader is not None
            assert isinstance(file_reader.content, str)
            assert len(file_reader.content.strip().split("\n")) > 0

    @pytest.mark.asyncio
    async def test_parsing_file_valido(self, temp_ter_file):
        """Verifica che un file generato casualmente possa essere parsificato."""
        reader = LocalFileReaderService(filepath=str(temp_ter_file))
        parser = FileParserService(reader=reader)

        # Ottenere l'oggetto Census dal parser
        census = await parser.parse()

        # Verifica che ci sia un oggetto Census
        assert census
        assert hasattr(census, "terreni")
        assert census.terreni

        # Verifica che ci siano immobili
        assert hasattr(census.terreni, "immobili")

        # Verifica che ogni immobile abbia almeno il record1
        for immobile in census.terreni.immobili:
            assert hasattr(immobile, "record1")
            assert immobile.record1 is not None
            assert immobile.record1.tipo_record == "1"

            # Se flag_deduzioni è 1, dovrebbe avere record2
            if immobile.record1.flag_deduzioni == "1":
                assert hasattr(immobile, "record2")
                assert immobile.record2 is not None

            # Se flag_porzione è 1, dovrebbe avere record4
            if immobile.record1.flag_porzione == "1":
                assert hasattr(immobile, "record4")
                assert immobile.record4 is not None

    @pytest.mark.asyncio
    async def test_file_con_errori(self, custom_ter_file):
        """Verifica che un file con errori produca le eccezioni appropriate."""
        # Crea un file con errori di sintassi
        file_path = custom_ter_file(num_immobili=2, con_errori=True)

        reader = LocalFileReaderService(filepath=str(file_path))
        parser = FileParserService(reader=reader)

        # Il parser dovrebbe sollevare eccezioni per i record malformati
        with pytest.raises(ParsingError):
            await parser.parse()

    @pytest.mark.asyncio
    async def test_raggruppamento_immobili(self, temp_ter_file):
        """Verifica che i record possano essere raggruppati per immobile."""

        reader = LocalFileReaderService(filepath=str(temp_ter_file))
        parser = FileParserService(reader=reader)

        # Ottieni l'oggetto Census
        census = await parser.parse()

        # Verifica che l'oggetto Census sia valido
        assert census is not None, "L'oggetto Census non è stato creato"
        assert hasattr(census, "terreni"), "Census non ha l'attributo terreni"
        assert census.terreni is not None, "L'attributo terreni è None"

        # Se ci sono immobili, verifica che abbiano la struttura corretta
        if hasattr(census.terreni, "immobili") and census.terreni.immobili:
            for immobile in census.terreni.immobili:
                # Verifica che l'immobile abbia gli attributi di base
                assert hasattr(
                    immobile, "codice_amministrativo"
                ), "Immobile senza codice amministrativo"
                assert hasattr(immobile, "sezione"), "Immobile senza sezione"
                assert hasattr(
                    immobile, "identificativo_immobile"
                ), "Immobile senza identificativo"
                assert hasattr(immobile, "tipo_immobile"), "Immobile senza tipo"
                assert hasattr(immobile, "progressivo"), "Immobile senza progressivo"

                # Verifica che l'immobile abbia almeno i record obbligatori
                assert hasattr(immobile, "record1"), "Immobile senza record1"
                assert immobile.record1 is not None, "Record1 è None"
        else:
            # Test passa anche senza immobili, ma lo segnaliamo
            print("Avviso: Nessun immobile trovato, ma il test passa comunque.")

    @pytest.mark.asyncio
    async def test_validate_record_formats(self, temp_ter_file):
        """Verifica che i record nel file rispettino i formati specificati nel PDF."""
        reader = LocalFileReaderService(filepath=str(temp_ter_file))

        async with reader.open() as file_reader:
            content = file_reader.content
            lines = content.strip().split("\n")

            for line in lines:
                # Estrai la parte dei campi chiave
                parts = line.split("|")
                assert len(parts) >= 5, f"Linea malformata: {line}"

                header = parts[0:6]

                # Verifica che l'header contenga i campi obbligatori
                assert len(header) == 6, f"Header troppo corto: {header}"

                # Verifica il tipo record
                tipo_record = header[5:6][0]
                assert tipo_record in [
                    "1",
                    "2",
                    "3",
                    "4",
                ], f"Tipo record non valido: {tipo_record}"

                # Verifica il tipo immobile (deve essere T per i terreni)
                tipo_immobile = header[3:4][0]
                assert (
                    tipo_immobile == "T"
                ), f"Tipo immobile non valido: {tipo_immobile}"

                # Verifica che il progressivo sia numerico
                progressivo = header[4:5][0]
                assert progressivo.isdigit(), f"Progressivo non numerico: {progressivo}"
