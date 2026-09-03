from pathlib import Path

import ibis
from loguru import logger


def create_connection(path_db: str) -> ibis.BaseBackend:
    logger.debug(
        f"Connecting to DuckDB at {path_db}",
    )
    database_path = Path(path_db)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    return ibis.duckdb.connect(database_path)
