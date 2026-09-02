from nicegui import ui

from varne.ui.layout import create_layout


@ui.page("/settings")
def page_settings() -> None:
    # TODO
    layout = create_layout()
    with layout:
        ui.label("Settings")
        [ui.label(f"Settings {i}") for i in range(100)]
