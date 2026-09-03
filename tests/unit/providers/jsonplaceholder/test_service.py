import pytest

from varne.providers.jsonplaceholder.client import JsonPlaceholderClient
from varne.providers.jsonplaceholder.service import JsonPlaceholderService


@pytest.mark.vcr
def test_store(db, http_client):
    client = JsonPlaceholderClient(http_client)
    service = JsonPlaceholderService(db=db, client=client)

    service.fetch_and_store()

    raw_count = db.table("raw").count().execute()
    staging_count = db.table("staging").count().execute()

    assert raw_count == 1
    assert staging_count == 100
