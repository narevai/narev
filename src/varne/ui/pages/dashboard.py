from nicegui import ui


@ui.page("/")
def page_dashboard() -> None:
    ui.label("Content")
    [ui.label(f"Line {i}") for i in range(100)]

    with ui.left_drawer(top_corner=True, bottom_corner=True, value=True).props(
        "breakpoint=768"
    ) as drawer:
        ui.label("left drawer")

    with ui.header(elevated=True):
        ui.button(icon="menu", on_click=drawer.toggle)
        ui.label("header")

    with ui.page_scroller(position="bottom-right", x_offset=20, y_offset=20):
        ui.button("Scroll to Top")
