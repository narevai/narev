import pytest

from varne.providers.jsonplaceholder.client import JsonPlaceholderClient
from varne.providers.jsonplaceholder.service import JsonPlaceholderService


@pytest.mark.vcr
def test_store(db, http_client):
    client = JsonPlaceholderClient(http_client)
    service = JsonPlaceholderService(db=db, client=client)

    service.fetch_and_store()

    raw = db.table("raw").execute()

    assert len(raw) == 1
    assert raw.iloc[0]["provider"] == "jsonplaceholder"
