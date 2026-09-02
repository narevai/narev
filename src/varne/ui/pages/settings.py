from nicegui import ui

from varne.ui.layout import create_layout


@ui.page("/settings")
def page_settings() -> None:
    # TODO
    layout = create_layout()
    with layout:
        ui.label("Settings").classes("text-2xl font-bold")
        [ui.label(f"Settings {i}") for i in range(100)]
