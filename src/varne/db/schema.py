import ibis
import ibis.expr.datatypes as dt


def get_schema_raw() -> ibis.schema:
    return ibis.schema(
        {"provider": dt.string, "event_time": dt.timestamp, "payload": dt.string}
    )


def create_tables(db: ibis.BaseBackend) -> None:
    existing_tables = set(db.list_tables())

    if "raw" not in existing_tables:
        schema = get_schema_raw()
        db.create_table("raw", schema=schema)
