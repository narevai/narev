from nicegui import ui


def register_pages() -> None:
    @ui.page("/")
    def index() -> None:
        with ui.column().classes(
            "w-full items-center justify-center min-h-screen gap-4"
        ):
            ui.icon("cloud", size="4rem").classes("text-primary")
            ui.label("Varne").classes("text-h3 font-bold")
            ui.label("FastAPI | NiceGUI | Ibis").classes("text-grey-7")
