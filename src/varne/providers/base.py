from abc import ABC, abstractmethod
from datetime import UTC, datetime

import httpx2 as httpx
import ibis

from varne.db.schema import TableRaw


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
        self.output_table = TableRaw()

    @abstractmethod
    def fetch_and_store(self) -> None:
        raise NotImplementedError()

    def store(self, payload: list[str]):
        self.db.insert(
            self.output_table.name,
            [
                {
                    "provider": "jsonplaceholder",
                    "event_time": datetime.now(UTC),
                    "payload": payload,
                }
            ],
        )
