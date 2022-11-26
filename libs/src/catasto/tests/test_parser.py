import pytest


@pytest.mark.asyncio
class TestFileParserService():

    async def test_parsing_cxf_file(self, cxf_parser):
        result = await cxf_parser.parse()
        breakpoint()
        assert result is not None
