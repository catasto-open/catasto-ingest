import pytest
from catasto.schemas.carto import HeaderModel, LandSheet


@pytest.mark.asyncio
class TestFileParserService:
    async def test_parse_name(self, cxf_parser):
        empty_land_sheet = LandSheet()
        parser = cxf_parser._parse_name(empty_land_sheet, "H501D076700")
        assert parser.codice_foglio == "H501D076700"
        assert parser.codice_comune == "H501"
        assert parser.codice_sezione_censuaria == "D"
        assert parser.codice_numero_foglio == "0767"
        assert parser.numero_foglio == "767"
        assert parser.codice_allegato == "0"
        assert parser.codice_sviluppo == "0"

    async def test_parse_header(self, cxf_parser, cxf_content_generator):
        parsed_name_land_sheet = LandSheet(
            codice_foglio="H501D076700",
            codice_comune="H501",
            codice_sezione_censuaria="D",
            codice_numero_foglio="0767",
            numero_foglio="767",
            codice_allegato="0",
            codice_sviluppo="0",
        )
        parser = cxf_parser._parse_header(parsed_name_land_sheet, cxf_content_generator)
        assert parser[0].header.mappa == "MAPPA"
        assert parser[0].header.nome_mappa == "H501D076700"
        assert parser[0].header.scala_originaria == "4000.000"

    async def test_parsing_cxf_file(self, cxf_parser):
        result = await cxf_parser.parse()
        assert result is not None
        expected = LandSheet(
            codice_foglio="H501D076700",
            codice_comune="H501",
            codice_sezione_censuaria="D",
            codice_numero_foglio="0767",
            numero_foglio="767",
            codice_allegato="0",
            codice_sviluppo="0",
            header=HeaderModel(
                mappa="MAPPA", nome_mappa="H501D076700", scala_originaria="4000.000"
            ),
        )

        # Confrontare l'intero oggetto con result
        assert result.codice_foglio == expected.codice_foglio
        assert result.codice_comune == expected.codice_comune
        assert result.codice_sezione_censuaria == expected.codice_sezione_censuaria
        assert result.codice_numero_foglio == expected.codice_numero_foglio
        assert result.numero_foglio == expected.numero_foglio
        assert result.codice_allegato == expected.codice_allegato
        assert result.codice_sviluppo == expected.codice_sviluppo
        assert result.header.mappa == expected.header.mappa
        assert result.header.nome_mappa == expected.header.nome_mappa
        assert result.header.scala_originaria == expected.header.scala_originaria
