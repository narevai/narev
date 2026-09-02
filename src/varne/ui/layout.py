from nicegui import ui
from nicegui.elements.column import Column


def create_layout() -> Column:
    with ui.left_drawer(top_corner=True, bottom_corner=True, value=True).props(
        "breakpoint=768"
    ) as drawer:
        ui.link("Dashboard", "/")
        ui.link("Integrations", "/integrations")
        ui.link("Settings", "/settings")

    with ui.header(elevated=True):
        ui.button(icon="menu", on_click=drawer.toggle)
        ui.label("Varne")

    with ui.page_scroller(position="bottom-right", x_offset=20, y_offset=20):
        ui.button("Scroll to Top")

    content = ui.column()

    return content
