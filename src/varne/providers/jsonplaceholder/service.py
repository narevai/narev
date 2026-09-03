from datetime import UTC, datetime

import ibis

from varne.providers.base import ProviderService
from varne.providers.jsonplaceholder.client import JsonPlaceholderClient
from varne.providers.jsonplaceholder.transform import transform_posts
from varne.providers.types import RowRaw, RowStaging


class JsonPlaceholderService(ProviderService):
    def __init__(self, db: ibis.BaseBackend, client: JsonPlaceholderClient):
        super().__init__(db)
        self.client = client

    def fetch_and_store(self) -> None:
        posts_payload: str = self.client.fetch_posts()
        posts_rows = [
            RowRaw(
                provider="jsonplaceholder",
                event_time=datetime.now(UTC),
                payload=posts_payload,
            )
        ]
        self.store_raw(posts_rows)
        posts_transformed: list[RowStaging] = transform_posts(posts_payload)
        self.store_staging(posts_transformed)
