from pathlib import Path

import ibis
from loguru import logger

from varne.config import get_settings

_connection: ibis.BaseBackend | None = None


def get_connection() -> ibis.BaseBackend:
    global _connection
    if _connection is None:
        settings = get_settings()
        _connection = create_connection(path_db=settings.database_path)
    return _connection


def create_connection(path_db: str) -> ibis.BaseBackend:
    logger.debug(
        f"Connecting to DuckDB at {path_db}",
    )
    database_path = Path(path_db)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    return ibis.duckdb.connect(database_path)
