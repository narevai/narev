from varne.providers.jsonplaceholder.client import JsonPlaceholderClient


def test_fetch(http_client):
    client = JsonPlaceholderClient(http_client)

    posts = client.fetch()

    assert len(posts) > 0
    assert posts[0]["id"]
