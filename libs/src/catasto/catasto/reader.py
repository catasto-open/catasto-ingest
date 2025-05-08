from typing import Protocol
from pathlib import Path
from contextlib import asynccontextmanager
import aiofiles
from miniopy_async import Minio
from .schemas.common import ReaderFile, UrlModel


class Reader(Protocol):

    filepath: str

    async def open(self) -> ReaderFile:
        pass

    def validate(self) -> bool:
        pass


class LocalFileReaderService(Reader):

    def __init__(self, filepath: str):
        self._filepath = filepath

    @asynccontextmanager
    async def open(self) -> ReaderFile:
        _filepath = Path(self._filepath)
        filename = _filepath.name
        filetype = _filepath.suffix
        if not _filepath.is_file():
            raise ValueError("Filepath is not a file")
        if not self.validate():
            raise ValueError(
                f"File type {filetype} is not valid"
            )
        async with aiofiles.open(_filepath, 'r') as _file:
            content = await _file.read()
            yield ReaderFile(
                filename=filename,
                filetype=filetype,
                content=content
            )

    def validate(self) -> bool:
        # @TODO: validate the file extension
        return True


class MinioFileReaderService(Reader):

    def __init__(
        self,
        filepath: str,
        key: str,
        secret: str,
        endpoint_url: str
    ):
        self._filepath = filepath
        self._key = key
        self._secret = secret
        self._endpoint_url = endpoint_url

    async def open(self) -> ReaderFile:
        _filepath = Path(self._filepath)
        filename = _filepath.name
        filetype = _filepath.suffix
        endpoint = UrlModel(url=self._endpoint_url)
        minio_client = Minio(
            f"{endpoint.url.host}:{endpoint.url.port}",
            access_key=self._key,
            secret_key=self._secret,
            secure=False
        )
        object_url = UrlModel(url=self._filepath)
        response = await minio_client.get_object(
            object_url.url.host,
            object_url.url.path            
        )
        content = await response.read()
        return ReaderFile(
            filename=filename,
            filetype=filetype,
            content=content.decode()
        )

    def validate(self) -> bool:
        # @TODO: validate the file extension
        return True
