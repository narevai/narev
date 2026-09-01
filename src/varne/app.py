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


def main() -> None:
    ui.run(
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        show=False,
    )


if __name__ in {"__main__", "__mp_main__"}:
    main()
