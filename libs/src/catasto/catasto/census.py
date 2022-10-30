from typing import Protocol
from py_scdb import AsyncStore
from .models import Census, CensusTypeEnum


class DictionariesBuilder(Protocol):

    name: str
    dictstore: AsyncStore
    dicts: Census

    async def store(self) -> AsyncStore:
        pass


class DictionariesBuilderService(DictionariesBuilder):

    async def __init__(
        self,
        name: str,
        dictstore: AsyncStore,
        dicts: Census
    ):
        self._name = name
        for item in CensusTypeEnum:
            self._dictstore = await dictstore.set(
                item.value, {}
            )
        self._dicts = dicts

    async def store(self) -> AsyncStore:
        pass