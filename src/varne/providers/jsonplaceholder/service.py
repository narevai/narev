import ibis

from varne.providers.base import ProviderService
from varne.providers.jsonplaceholder.client import JsonPlaceholderClient


class JsonPlaceholderService(ProviderService):
    def __init__(self, db: ibis.BaseBackend, client: JsonPlaceholderClient):
        super().__init__(db)
        self.client = client

    def fetch_and_store(self) -> None:
        posts = self._fetch_posts()
        self.store(posts)

    def _fetch_posts(self):
        return self.client.fetch_posts()
