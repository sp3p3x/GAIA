import flet as ft
import time

DEBUG = True


def debug(*args):
    if DEBUG:
        print(args)


class Animation:

    def fade_in_out(widget):
        time.sleep(0.1)
        widget.opacity = 1
        widget.update()
        time.sleep(2)
        widget.opacity = 0
        widget.update()
        widget.clean()
        time.sleep(0.3)


class Functions:

    def roomNumberIsValid(roomNum):
        if len(roomNum) > 3:
            return True
        else:
            return False


class Pages:

    fromRoomNumber = None
    toRoomNumber = None

    mapImage = ft.Image(
        src="foo/mapPlaceholder.jpg",
        fit=ft.ImageFit.FILL,
    )

    def updateMapSize(app, width, height):
        Pages.mapImage.width = width
        Pages.mapImage.height = height - 80
        app.page.go("/inputPage")

    def rootpage(app):
        return ft.View(
            "/",
            [
                ft.AppBar(
                    title=ft.Text("Main Menu"), bgcolor=ft.colors.SURFACE_VARIANT
                ),
                ft.ElevatedButton(
                    "Navigate", on_click=lambda _: app.page.go("/inputPage")
                ),
            ],
        )

    def inputPage(app):
        mapImage = Pages.mapImage
        Pages.updateMapSize(app, app.page.window_width, app.page.window_height)

        def getRoomNum(e):
            global fromRoomNumber
            global toRoomNumber
            fromRoomNumber = fromRoomInput.value
            toRoomNumber = toRoomInput.value
            if Functions.roomNumberIsValid(
                fromRoomNumber
            ) and Functions.roomNumberIsValid(toRoomNumber):
                debug(fromRoomNumber, toRoomNumber)
                app.page.go("/pathPage")
            else:
                notValidInputWarning.open = True
                app.page.update()
                debug("input insufficient")

        notValidInputWarning = ft.SnackBar(
            content=ft.Text("Please enter a valid Room Number!"), action="Got it!"
        )

        fromRoomInput = ft.TextField(
            label="From",
            hint_text="Enter Room Number",
            on_submit=getRoomNum,
            autofocus=True,
            border_radius=50,
            text_size=15,
            bgcolor=ft.colors.BACKGROUND,
            border_width=0.3,
        )

        toRoomInput = ft.TextField(
            label="To",
            hint_text="Enter Room Number",
            on_submit=getRoomNum,
            border_radius=50,
            text_size=15,
            bgcolor=ft.colors.BACKGROUND,
            border_width=0.3,
        )

        return ft.View(
            "/inputPage",
            [
                ft.AppBar(title=ft.Text("Input"), bgcolor=ft.colors.SURFACE_VARIANT),
                ft.Container(
                    ft.Stack(
                        [
                            mapImage,
                            ft.Column(
                                [
                                    fromRoomInput,
                                    toRoomInput,
                                ],
                            ),
                        ]
                    ),
                    padding=0,
                    border_radius=10,
                ),
                notValidInputWarning,
                # ft.ElevatedButton("Next", on_click=getRoomNum),
            ],
        )

    def pathPage(app):
        global fromRoomNumber
        global toRoomNumber

        return ft.View(
            "/pathPage",
            [
                ft.AppBar(title=ft.Text("Path"), bgcolor=ft.colors.SURFACE_VARIANT),
                ft.Text(fromRoomNumber),
                ft.Text(toRoomNumber),
                ft.ElevatedButton("Next", on_click=lambda _: app.page.go("/")),
            ],
        )


class Main:

    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "GAIA"
        # self.page.window_maximized = True
        self.page.vertical_alignment = ft.MainAxisAlignment.CENTER
        self.page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        # self.splash()
        self.main()

    def view_pop(self, view):
        self.page.views.pop()
        top_view = self.page.views[-1]
        self.page.go(top_view.route)

    def splash(self):
        self.page.clean()
        splash = ft.Image(
            src="assets/logo.png",
            width=1000,
            height=500,
            fit=ft.ImageFit.CONTAIN,
            opacity=0,
            animate_opacity=400,
        )
        self.page.add(splash)
        Animation.fade_in_out(splash)

    def route_change(self, route):
        self.page.views.clear()
        self.page.views.append(Pages.rootpage(self))
        if self.page.route == "/inputPage":
            self.page.views.append(Pages.inputPage(self))
        if self.page.route == "/pathPage":
            self.page.views.append(Pages.pathPage(self))
        self.page.update()

    def pageResize(self, event):
        Pages.updateMapSize(self, self.page.window_width, self.page.window_height)

    def main(self):
        self.page.on_resize = self.pageResize
        self.page.on_route_change = self.route_change
        self.page.on_view_pop = self.view_pop
        # self.page.go(self.page.route)
        self.page.go("/inputPage")


ft.app(target=Main)
