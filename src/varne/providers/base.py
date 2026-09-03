from abc import ABC, abstractmethod

import httpx2 as httpx
import ibis

from varne.db.schema import TableRaw, TableStaging
from varne.providers.types import RowRaw, RowStaging


class ProviderClient(ABC):
    def __init__(
        self,
        http: httpx.Client,
    ) -> None:
        self.http = http

    @property
    @abstractmethod
    def base_url(self) -> str:
        raise NotImplementedError()


class ProviderService(ABC):
    def __init__(self, db: ibis.BaseBackend) -> None:
        self.db = db
        self.raw_table = TableRaw()
        self.staging_table = TableStaging()

    @abstractmethod
    def fetch_and_store(self) -> None:
        raise NotImplementedError()

    def store_raw(self, rows: list[RowRaw]):
        payload = [row.model_dump() for row in rows]
        self.db.insert(self.raw_table.name, payload)

    def store_staging(self, rows: list[RowStaging]):
        payload = [row.model_dump() for row in rows]
        self.db.insert(self.staging_table.name, payload)
