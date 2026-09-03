from loguru import logger
from nicegui import run, ui

from varne.analytics.usage import get_usage_by_id
from varne.dependencies import get_db, get_json_placeholder_service
from varne.ui.layout import create_layout


def get_usage_rows(db) -> list[dict]:
    result = get_usage_by_id(db).execute()
    return result.to_dict("records")


@ui.page("/")
async def page_dashboard() -> None:
    layout = create_layout()
    db = get_db()
    with layout:
        ui.label("Dashboard").classes("text-2xl font-bold")
        columns = [
            {
                "name": "id",
                "label": "ID",
                "field": "id",
                "align": "left",
            },
            {
                "name": "total_amount",
                "label": "Total Amount",
                "field": "total_amount",
                "align": "right",
            },
        ]
        table = ui.table(
            columns=columns,
            rows=[],
            row_key="id",
        )

        async def refresh_table() -> None:
            table.rows = await run.io_bound(get_usage_rows, db)

        async def sync_usage() -> None:
            service = get_json_placeholder_service()

            button.disable()

            try:
                _ = await run.io_bound(service.fetch_and_store)
                await refresh_table()
                ui.notify("Synced rows")

            except Exception as ex:
                logger.error(f"Sync failed {ex}")
                ui.notify("Sync failed.", type="negative")

            finally:
                button.enable()

        button = ui.button("sync", on_click=sync_usage)
        await refresh_table()
