import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> TestClient:
    from varne.app import app

    return TestClient(app)
