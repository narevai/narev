import ibis

from varne.providers.base import ProviderService
from varne.providers.jsonplaceholder.client import JsonPlaceholderClient
from varne.providers.jsonplaceholder.transform import transform_posts


class JsonPlaceholderService(ProviderService):
    def __init__(self, db: ibis.BaseBackend, client: JsonPlaceholderClient):
        super().__init__(db)
        self.client = client

    def fetch_and_store(self) -> None:
        posts = self.client.fetch_posts()
        self.store_raw(posts)
        posts_transformed = transform_posts(posts)
        self.store_staging(posts_transformed)
