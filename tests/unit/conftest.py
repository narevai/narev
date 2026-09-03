import pytest
from fastapi.testclient import TestClient

from varne.db.connection import create_connection
from varne.db.schema import create_tables


@pytest.fixture
def client() -> TestClient:
    from varne.app import app

    return TestClient(app)


@pytest.fixture
def db(tmp_path):
    path_db = tmp_path / "test.duckdb"
    connection = create_connection(path_db)

    create_tables(connection)
    yield connection
