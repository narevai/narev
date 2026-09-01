import sys

from loguru import logger
from nicegui import app, ui

from varne.api.v1 import router
from varne.config import get_settings
from varne.ui.pages.dashboard import register_pages

settings = get_settings()

logger.remove()
logger.add(sys.stderr, level=settings.log_level)

app.include_router(router, prefix="/api/v1")
register_pages()

ui.run(host="0.0.0.0", port=8000, reload=True)
