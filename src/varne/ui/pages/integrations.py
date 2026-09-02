from nicegui import ui

from varne.ui.layout import create_layout


@ui.page("/integrations")
def page_integrations() -> None:
    # TODO
    layout = create_layout()
    with layout:
        ui.label("Integrations").classes("text-2xl font-bold")
        [ui.label(f"Integration {i}") for i in range(100)]
