import pytest
from fastapi.testclient import TestClient

from varne.app import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
