import pytest
from catasto.schemas.carto import LandSheet


@pytest.mark.asyncio
class TestFileParserService():

    async def test_parse_name(self, cxf_parser):
        empty_land_sheet = LandSheet()
        parser = cxf_parser._parse_name(
            empty_land_sheet, "H501D076700"
        )
        assert parser.codice_foglio == "H501D076700"
        assert parser.codice_comune == "H501"
        assert parser.codice_sezione_censuaria == "D"
        assert parser.codice_numero_foglio == "0767"
        assert parser.numero_foglio == "767"
        assert parser.codice_allegato == "0"
        assert parser.codice_sviluppo == "0"


    async def test_parsing_cxf_file(self, cxf_parser):
        result = await cxf_parser.parse()
        breakpoint()
        assert result is not None
        assert result == LandSheet(
            codice_foglio="H501D076700",
            codice_comune="H501",
            codice_sezione_censuaria="D",
            codice_numero_foglio="0767",
            numero_foglio="767",
            codice_allegato="0",
            codice_sviluppo="0"
        )
