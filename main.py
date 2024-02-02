import flet as ft
import time

class Animation():

    def fade_in_out(widget):
        time.sleep(0.1)
        widget.opacity = 1
        widget.update()
        time.sleep(2)
        widget.opacity = 0
        widget.update()
        widget.clean()
        time.sleep(0.3)


class UI():
    
    def __init__(self,page):
        self.page = page

    def route_change(self):
        self.page.views.clear()
        self.page.views.append(
            ft.View(
                "/",
                [
                    ft.AppBar(title=ft.Text("From"), bgcolor=ft.colors.SURFACE_VARIANT),
                    ft.TextField(label="From", hint_text="Enter Room Number"),
                    ft.ElevatedButton("Next", on_click=lambda _: self.page.go("/fromPage")),
                ],
            )
        )
        if self.page.route == "/fromPage":
            self.page.views.append(
                ft.View(
                    "/fromPage",
                    [
                        ft.AppBar(title=ft.Text("To"), bgcolor=ft.colors.SURFACE_VARIANT),
                        ft.TextField(label="To", hint_text="Enter Room Number"),
                        ft.ElevatedButton("Next", on_click=lambda _: self.page.go("/")),
                    ],
                )
            )
        self.page.update()


class Main():

    def __init__(self,page: ft.Page):
        self.page = page
        self.page.title = "GAIA"
        self.page.window_maximized  = True
        self.page.vertical_alignment = ft.MainAxisAlignment.CENTER
        self.page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.splash()
        self.main()

    def view_pop(self,view):
        self.page.views.pop()
        top_view = self.page.views[-1]
        self.page.go(top_view.route)

    def splash(self):
        self.page.clean()
        splash = ft.Image(src="assets/logo.png", width=1000, height=500, fit=ft.ImageFit.CONTAIN, opacity=0, animate_opacity=400)
        self.page.add(splash)
        Animation.fade_in_out(splash)

    def main(self):

        UI(self.page)

        self.page.on_route_change = UI.route_change
        self.page.on_view_pop = self.view_pop
        self.page.go(self.page.route)
        # self.page.go("/fromPage")


ft.app(target=Main)