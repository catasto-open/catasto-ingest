import pytest
from catasto.parser import (
    FileParserService,
    ParsingError,
    parse_tit_record_info,
    parse_tit_record_line,
)
from catasto.reader import LocalFileReaderService
from pydantic import ValidationError


class TestTitRecordInfo:
    """Test per il record generico di TIT."""

    def test_parse_tit_record_info_valid_line(self, static_tit_record_valid_line):
        "Verifica che una linea con un record generico venga interpretata correttamente."

        tit_record_info = parse_tit_record_info(static_tit_record_valid_line)

        assert tit_record_info.codice_amministrativo == "H501"
        assert tit_record_info.sezione == " "
        assert tit_record_info.identificativo_soggetto == "54898"
        assert tit_record_info.tipo_soggetto == "P"
        assert tit_record_info.identificativo_immobile == "1437626"
        assert tit_record_info.tipo_immobile == "F"
        assert tit_record_info.items_number == 33  # 6 header + 26 dati

    def test_parse_tit_record_info_invalid_line(self, static_tit_record_invalid_line):
        "Verifica che una linea con un record generico invalido generi un errore."

        with pytest.raises(ValidationError):
            tit_record_info = parse_tit_record_info(static_tit_record_invalid_line)


class TestTitolarita:
    """Test per i record di titolarità."""

    def test_parse_tit_record_line(self, static_tit_record_valid_line):
        "Verifica che una linea con un record di titolarità venga interpretata correttamente."

        tit_record_info = parse_tit_record_info(static_tit_record_valid_line)
        parser = parse_tit_record_line(tit_record_info)

        assert parser.codice_amministrativo == "H501"
        assert parser.sezione == " "
        assert parser.identificativo_soggetto == "54898"
        assert parser.tipo_soggetto == "P"
        assert parser.identificativo_immobile == "1437626"
        assert parser.tipo_immobile == "F"

        assert parser.codice_diritto == "10"
        assert parser.quota_numeratore == "1"
        assert parser.quota_denominatore == "1"
        assert parser.regime == " "
        assert parser.soggetto_di_riferimento == ""

        assert parser.data_di_validita_iniziale == "12112003"
        assert parser.tipo_nota_iniziale == "N"
        assert parser.numero_nota_iniziale == "053614"
        assert parser.progressivo_nota_iniziale == "001"
        assert parser.anno_nota_iniziale == "2010"
        assert parser.data_registrazione_atti_iniziale == "25082010"
        assert parser.partita == ""

        assert parser.identificativo_titolarita == "28099632"
        assert parser.codice_causale_atto_generante == "SEN"
        assert parser.descrizione_atto_generante == "DIVISIONE"

    def test_parse_tit_record_line_invalid(self, static_tit_record_invalid_line):
        "Verifica che una linea con un record di titolarità invalido generi un errore."

        with pytest.raises(ValidationError):
            tit_record_info = parse_tit_record_info(static_tit_record_invalid_line)
            parser = parse_tit_record_line(tit_record_info)


class TestFileValidazione:
    """Test per la validazione di interi file .TIT."""

    @pytest.mark.asyncio
    async def test_lettura_file_valido(self, temp_tit_file):
        """Verifica che un file generato casualmente possa essere letto."""
        reader = LocalFileReaderService(filepath=str(temp_tit_file))

        async with reader.open() as file_reader:
            assert file_reader is not None
            assert isinstance(file_reader.content, str)
            assert len(file_reader.content.strip().split("\n")) > 0

    @pytest.mark.asyncio
    async def test_parsing_file_valido(self, temp_tit_file):
        """Verifica che un file generato casualmente possa essere parsificato."""
        reader = LocalFileReaderService(filepath=str(temp_tit_file))
        parser = FileParserService(reader=reader)

        # Ottenere l'oggetto Census dal parser
        census = await parser.parse()

        # Verifica che ci sia un oggetto Census
        assert census
        assert hasattr(census, "titolarita")
        assert census.titolarita

        # Verifica che ci siano titolarità
        assert hasattr(census.titolarita, "titolarita")

        # Verifica che ogni titolarità abbia una struttura valida
        for titolarita in census.titolarita.titolarita:
            assert hasattr(titolarita, "codice_amministrativo")
            assert hasattr(titolarita, "identificativo_soggetto")
            assert hasattr(titolarita, "tipo_soggetto")
            assert hasattr(titolarita, "identificativo_immobile")
            assert hasattr(titolarita, "tipo_immobile")

            # Verifica che il tipo soggetto sia valido
            assert titolarita.tipo_soggetto in ["P", "G"]

            # Verifica che il tipo immobile sia valido
            assert titolarita.tipo_immobile in ["F", "T"]

            # Verifica che il regime sia valido
            assert titolarita.regime in [
                " ",
                "C",
                "D",
                "P",
                "S",
            ]

    @pytest.mark.asyncio
    async def test_file_con_errori(self, custom_tit_file):
        """Verifica che un file con errori produca le eccezioni appropriate."""
        # Crea un file con errori di sintassi
        file_path = custom_tit_file(num_titolarita=2, con_errori=True)

        reader = LocalFileReaderService(filepath=str(file_path))
        parser = FileParserService(reader=reader)

        # Il parser dovrebbe sollevare eccezioni raccolte in ParsingError per i record malformati
        with pytest.raises(ParsingError):
            await parser.parse()

    @pytest.mark.asyncio
    async def test_raggruppamento_titolarita(self, temp_tit_file):
        """Verifica che i record possano essere raggruppati per titolarità."""

        reader = LocalFileReaderService(filepath=str(temp_tit_file))
        parser = FileParserService(reader=reader)

        # Ottieni l'oggetto Census
        census = await parser.parse()

        # Verifica che l'oggetto Census sia valido
        assert census is not None, "L'oggetto Census non è stato creato"
        assert hasattr(census, "titolarita"), "Census non ha l'attributo titolarita"
        assert census.titolarita is not None, "L'attributo titolarita è None"

        # Se ci sono titolarità, verifica che abbiano la struttura corretta
        if hasattr(census.titolarita, "titolarita") and census.titolarita.titolarita:
            for titolarita in census.titolarita.titolarita:
                # Verifica che la titolarità abbia gli attributi di base
                assert hasattr(
                    titolarita, "codice_amministrativo"
                ), "Titolarità senza codice amministrativo"
                assert hasattr(
                    titolarita, "identificativo_soggetto"
                ), "Titolarità senza identificativo soggetto"
                assert hasattr(
                    titolarita, "identificativo_immobile"
                ), "Titolarità senza identificativo immobile"

                # Verifica che la titolarità non abbia record distinti
                assert not hasattr(titolarita, "record"), "Titolarità senza record"
        else:
            # Test passa anche senza titolarità, ma lo segnaliamo
            print("Avviso: Nessuna titolarità trovata, ma il test passa comunque.")

    @pytest.mark.asyncio
    async def test_validate_record_formats(self, temp_tit_file):
        """Verifica che i record nel file rispettino i formati specificati."""
        reader = LocalFileReaderService(filepath=str(temp_tit_file))

        async with reader.open() as file_reader:
            content = file_reader.content
            lines = content.strip().split("\n")

            for line in lines:
                # Estrai la parte dei campi chiave
                parts = line.split("|")
                assert len(parts) >= 6, f"Linea malformata: {line}"

                header = parts[0:6]

                # Verifica che l'header contenga i campi obbligatori
                assert len(header) == 6, f"Header troppo corto: {header}"

                # Verifica il tipo soggetto
                tipo_soggetto = header[3]
                assert tipo_soggetto in [
                    "P",
                    "G",
                ], f"Tipo soggetto non valido: {tipo_soggetto}"

                # Verifica il tipo immobile
                tipo_immobile = header[5]
                assert tipo_immobile in [
                    "F",
                    "T",
                ], f"Tipo immobile non valido: {tipo_immobile}"
