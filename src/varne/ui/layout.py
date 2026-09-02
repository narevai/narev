from nicegui import ui
from nicegui.elements.column import Column

from varne.ui.components.nav_item import nav_item


def create_layout() -> Column:
    with ui.left_drawer(top_corner=True, bottom_corner=True, value=True).props(
        "breakpoint=768"
    ) as drawer:
        nav_item("Dashboard", "menu", "/")
        nav_item("Integrations", "extension", "/integrations")
        nav_item("Settings", "settings", "/settings")

        # ui.link("Dashboard", "/")
        # ui.link("Integrations", "/integrations")
        # ui.link("Settings", "/settings")

    with ui.header(elevated=True):
        ui.button(icon="menu", on_click=lambda: drawer.toggle())
        ui.label("Varne")

    with ui.page_scroller(position="bottom-right", x_offset=20, y_offset=20):
        ui.button("Scroll to Top")

    content = ui.column()

    return content
