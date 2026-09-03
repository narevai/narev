import httpx2 as httpx


def create_http_client() -> httpx.Client:
    timeout = httpx.Timeout(connect=10.0, read=30.0, write=30.0, pool=5.0)

    limits = httpx.Limits(max_connections=20, max_keepalive_connections=10)

    transport = httpx.HTTPTransport(retries=3)

    headers = {
        "User-Agent": "varne/0.1",
        "Accept": "application/json",
    }

    client = httpx.Client(
        timeout=timeout,
        limits=limits,
        transport=transport,
        follow_redirects=True,
        headers=headers,
    )

    return client
