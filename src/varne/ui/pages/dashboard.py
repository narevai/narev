from nicegui import ui

from varne.ui.layout import create_layout


@ui.page("/")
def page_dashboard() -> None:
    # TODO
    layout = create_layout()
    with layout:
        ui.label("Dashboard")
        [ui.label(f"Dashboard {i}") for i in range(100)]
