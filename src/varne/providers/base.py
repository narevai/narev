from abc import ABC, abstractmethod

import httpx2 as httpx


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

    @abstractmethod
    def fetch(self) -> list[dict]:
        raise NotImplementedError()
