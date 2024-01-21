import flet as ft

def main(page: ft.Page):
    page.title = "GAIA"
    page.theme = page.dark_theme

    page.add(
      ft.Text("Hello World"),
    )

    page.update()

ft.app(target=main)