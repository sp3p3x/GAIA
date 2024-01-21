import flet as ft
import time

class Animation():

    def fade_in_out(widget):
        widget.opacity = 1
        widget.update()
        time.sleep(2)
        widget.opacity = 0
        widget.update()
        widget.clean()

class UI():

    def __init__(self,page: ft.Page):
        self.page = page
        self.page.title = "GAIA"
        self.page.theme = page.dark_theme
        self.page.vertical_alignment = ft.MainAxisAlignment.CENTER
        self.page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.splash()

    def splash(self):
        self.page.clean()
        splash = ft.Image(src="assets/logo.png", width=1000, height=500, fit=ft.ImageFit.CONTAIN, opacity=0, animate_opacity=400)
        self.page.add(splash)
        time.sleep(0.2)
        Animation.fade_in_out(splash)

ft.app(target=UI)