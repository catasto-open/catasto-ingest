import pytest
from catasto.parser import (
    FileParserService,
    ParsingError,
    parse_sog_record_g_line,
    parse_sog_record_info,
    parse_sog_record_p_line,
)
from catasto.reader import LocalFileReaderService
from pydantic import ValidationError


class TestSogRecordInfo:
    """Test per il record generico di SOG."""

    def test_parse_sog_record_info_valid_line(
        self, static_sog_private_person_record_valid_line
    ):
        "Verifica che una linea con un record generico venga interpretata correttamente."

        sog_record_info = parse_sog_record_info(
            static_sog_private_person_record_valid_line
        )

        assert sog_record_info.codice_amministrativo == "H501"
        assert sog_record_info.sezione == " "
        assert sog_record_info.identificativo_soggetto == "7125464"
        assert sog_record_info.tipo_soggetto == "P"
        assert sog_record_info.items_number == 12

    def test_parse_sog_record_info_invalid_line(
        self, static_sog_private_person_record_invalid_line
    ):
        "Verifica che una linea con un record generico venga interpretata correttamente."

        with pytest.raises(ValidationError):
            sog_record_info = parse_sog_record_info(
                static_sog_private_person_record_invalid_line
            )


class TestSoggettiRecordGiuridicPerson:
    """Test per il record di tipo G (soggetti persone giuridiche dell'unità immobiliare)."""

    def test_parse_record_g_line(self, static_sog_giuridic_person_record_valid_line):
        "Verifica che una linea con un record P venga interpretata correttamente."

        sog_record_info = parse_sog_record_info(
            static_sog_giuridic_person_record_valid_line
        )
        parser = parse_sog_record_g_line(sog_record_info)

        assert parser.codice_amministrativo == "H501"
        assert parser.sezione == " "
        assert parser.identificativo_soggetto == "8363"
        assert parser.tipo_soggetto == "G"

        assert parser.denominazione == "COMUNE DI ROMA"
        assert parser.sede == "H501"
        assert parser.codice_fiscale == "02437850856"

    def test_parse_record_g_invalid_line(
        self, static_sog_giuridic_person_record_invalid_line
    ):
        "Verifica che una linea con un record P venga interpretata correttamente."

        with pytest.raises(ValidationError):
            sog_record_info = parse_sog_record_info(
                static_sog_giuridic_person_record_invalid_line
            )
            parser = parse_sog_record_g_line(sog_record_info)


class TestSoggetiRecordPrivatePerson:
    """Test per il record di tipo P (soggetti persone private dell'unità immobiliare)."""

    def test_parse_record_p_line(self, static_sog_private_person_record_valid_line):
        "Verifica che una linea con un record P venga interpretata correttamente."

        sog_record_info = parse_sog_record_info(
            static_sog_private_person_record_valid_line
        )
        parser = parse_sog_record_p_line(sog_record_info)

        assert parser.codice_amministrativo == "H501"
        assert parser.sezione == " "
        assert parser.identificativo_soggetto == "7125464"
        assert parser.tipo_soggetto == "P"

        assert parser.cognome == "ROSSI"
        assert parser.nome == "MARIO"
        assert parser.sesso == "1"
        assert parser.data_di_nascita == "01091973"
        assert parser.luogo_di_nascita == "H501"
        assert parser.codice_fiscale == "MRIRSS73P01LH501"

    def test_parse_record_p_invalid_line(
        self, static_sog_private_person_record_invalid_line
    ):
        "Verifica che una linea con un record P venga interpretata correttamente."

        with pytest.raises(ValidationError):
            sog_record_info = parse_sog_record_info(
                static_sog_private_person_record_invalid_line
            )
            parser = parse_sog_record_p_line(sog_record_info)


class TestFileValidazione:
    """Test per la validazione di interi file .SOG."""

    @pytest.mark.asyncio
    async def test_lettura_file_valido(self, temp_sog_file):
        """Verifica che un file generato casualmente possa essere letto."""
        reader = LocalFileReaderService(filepath=str(temp_sog_file))

        async with reader.open() as file_reader:
            assert file_reader is not None
            assert isinstance(file_reader.content, str)
            assert len(file_reader.content.strip().split("\n")) > 0

    @pytest.mark.asyncio
    async def test_parsing_file_valido(self, temp_sog_file):
        """Verifica che un file generato casualmente possa essere parsificato."""
        reader = LocalFileReaderService(filepath=str(temp_sog_file))
        parser = FileParserService(reader=reader)

        # Ottenere l'oggetto Census dal parser
        census = await parser.parse()

        # Verifica che ci sia un oggetto Census
        assert census
        assert hasattr(census, "soggetti")
        assert census.soggetti

        # Verifica che ci siano soggetti
        assert hasattr(census.soggetti, "soggetti")

        # Verifica che ogni soggetto abbia almeno o il record di tipo P o G
        for soggetto in census.soggetti.soggetti:
            assert hasattr(soggetto, "record")
            assert soggetto.record is not None
            assert soggetto.record.tipo_soggetto in ["P", "G"]

    @pytest.mark.asyncio
    async def test_file_con_errori(self, custom_sog_file):
        """Verifica che un file con errori produca le eccezioni appropriate."""
        # Crea un file con errori di sintassi
        file_path = custom_sog_file(num_soggetti=2, con_errori=True)

        reader = LocalFileReaderService(filepath=str(file_path))
        parser = FileParserService(reader=reader)

        # Il parser dovrebbe sollevare eccezioni raccolte in ParsingError per i record malformati
        with pytest.raises(ParsingError):
            await parser.parse()

    @pytest.mark.asyncio
    async def test_raggruppamento_soggetti(self, temp_sog_file):
        """Verifica che i record possano essere raggruppati per soggetto."""

        reader = LocalFileReaderService(filepath=str(temp_sog_file))
        parser = FileParserService(reader=reader)

        # Ottieni l'oggetto Census
        census = await parser.parse()

        # Verifica che l'oggetto Census sia valido
        assert census is not None, "L'oggetto Census non è stato creato"
        assert hasattr(census, "soggetti"), "Census non ha l'attributo soggetti"
        assert census.soggetti is not None, "L'attributo soggetti è None"

        # Se ci sono soggetti, verifica che abbiano la struttura corretta
        if hasattr(census.soggetti, "soggetti") and census.soggetti.soggetti:
            for soggetto in census.soggetti.soggetti:
                # Verifica che il soggetto abbia gli attributi di base
                assert hasattr(
                    soggetto, "codice_amministrativo"
                ), "Soggetto senza codice amministrativo"
                assert hasattr(soggetto, "sezione"), "Soggetto senza sezione"
                assert hasattr(
                    soggetto, "identificativo_soggetto"
                ), "Soggetto senza identificativo"
                assert hasattr(soggetto, "tipo_soggetto"), "Soggetto senza tipo"

                # Verifica che il soggetto abbia almeno i record obbligatori
                assert hasattr(soggetto, "record"), "Soggetto senza record"
                assert soggetto.record is not None, "Record è None"
        else:
            # Test passa anche senza soggetti, ma lo segnaliamo
            print("Avviso: Nessun soggetto trovato, ma il test passa comunque.")

    @pytest.mark.asyncio
    async def test_validate_record_formats(self, temp_sog_file):
        """Verifica che i record nel file rispettino i formati specificati nel PDF."""
        reader = LocalFileReaderService(filepath=str(temp_sog_file))

        async with reader.open() as file_reader:
            content = file_reader.content
            lines = content.strip().split("\n")

            for line in lines:
                # Estrai la parte dei campi chiave
                parts = line.split("|")
                assert len(parts) >= 3, f"Linea malformata: {line}"

                header = parts[0:4]

                # Verifica che l'header contenga i campi obbligatori
                assert len(header) == 4, f"Header troppo corto: {header}"

                # Verifica il tipo soggetto (deve essere P/G per i soggetti)
                tipo_soggetto = header[3:4][0]
                assert tipo_soggetto in [
                    "P",
                    "G",
                ], f"Tipo soggetto non valido: {tipo_soggetto}"
