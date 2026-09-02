from nicegui import ui


def nav_item(label: str, icon: str, target: str):
    with ui.item(on_click=lambda: ui.navigate.to(target)).classes("w-full rounded"):
        with ui.item_section().props("side"):
            ui.icon(icon).classes("text-sm")
        with ui.item_section():
            ui.label(label).classes("text-sm")
