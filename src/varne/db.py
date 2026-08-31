from pathlib import Path

import ibis
from loguru import logger

from varne.config import get_settings

_connection: ibis.BaseBackend | None = None


def get_connection() -> ibis.BaseBackend:
    global _connection
    if _connection is None:
        settings = get_settings()
        logger.debug("Connecting to DuckDB at {}", settings.database_path)
        database_path = Path(settings.database_path)
        database_path.parent.mkdir(parents=True, exist_ok=True)
        _connection = ibis.duckdb.connect(database_path)
    return _connection
