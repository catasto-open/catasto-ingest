import pytest
from catasto.schemas.common import ReaderFile


@pytest.mark.asyncio
class TestLocalFileReaderService():

    async def test_open_file(self, local_file_reader):
        async with local_file_reader.open() as reader:
            assert reader is not None
            assert reader == ReaderFile(
                filename="textfile.SOG",
                filetype=".SOG",
                content="Hello|Catasto|2021\nHello|Catasto|2022"
            )


    async def test_error_open_not_a_file(self, local_dir_reader):
        with pytest.raises(ValueError):
            async with local_dir_reader.open() as reader:
                assert reader is not None
