from varne.http import create_http_client


def test_create_http_client():
    with create_http_client() as http_client:
        response = http_client.get("https://jsonplaceholder.typicode.com/todos/1")

    assert response.status_code == 200


def test_connect_http_client(http_client):
    response = http_client.get("https://jsonplaceholder.typicode.com/todos/1")
    assert response.status_code == 200
