from varne.db.connection import get_connection


def test_ibis_connection():
    conn = get_connection()
    result = conn.sql("SELECT 1 AS value").execute()
    assert result["value"].iloc[0] == 1


def test_db_table_create(db):
    assert db.list_tables() == ["raw"]
