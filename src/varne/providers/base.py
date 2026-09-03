from abc import ABC, abstractmethod
from datetime import UTC, datetime

import httpx2 as httpx
import ibis

from varne.db.schema import TableRaw, TableStaging


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

    def store_raw(self, payload: list[str]):
        self.db.insert(
            self.raw_table.name,
            [
                {
                    "provider": "jsonplaceholder",
                    "event_time": datetime.now(UTC),
                    "payload": payload,
                }
            ],
        )

    def store_staging(self, payload: list[str]):
        self.db.insert(
            self.staging_table.name,
            [
                {
                    "provider": "jsonplaceholder",
                    "event_time": datetime.now(UTC),
                    "amount": payload,
                }
            ],
        )
