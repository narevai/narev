from abc import ABC, abstractmethod

import ibis
import ibis.expr.datatypes as dt


class Table(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError()

    @property
    @abstractmethod
    def schema(self) -> ibis.schema:
        raise NotImplementedError()


class TableRaw(Table):
    @property
    def name(self):
        return "raw"

    @property
    def schema(self) -> ibis.schema:
        return ibis.schema(
            {"provider": dt.string, "event_time": dt.timestamp, "payload": dt.string}
        )


class TableStaging(Table):
    @property
    def name(self):
        return "staging"

    @property
    def schema(self) -> ibis.schema:
        return ibis.schema(
            {"id": dt.string, "event_time": dt.timestamp, "amount": dt.float}
        )


TABLES: list[type[Table]] = [TableRaw(), TableStaging()]


def create_tables(db: ibis.BaseBackend) -> None:
    existing_tables = set(db.list_tables())

    for table in TABLES:
        if table.name not in existing_tables:
            db.create_table(table.name, schema=table.schema)
