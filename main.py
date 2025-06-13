import threading, time, cv2, re
import flet as ft
from PIL import Image, ImageDraw, ImageFont
from collections import deque
import numpy as np

DEBUG = True


def debug(data):
    if DEBUG:
        print(f"{time.strftime('%H:%M:%S', time.gmtime())}: {data}\n")


class TracePath:
    def __init__(self):
        self.tile_size = 300
        self.transparent = cv2.imread(
            "assets/mapComp/transparent.png", cv2.IMREAD_UNCHANGED
        )
        self.trace = cv2.imread("assets/mapComp/trace.png", cv2.IMREAD_UNCHANGED)

        if self.transparent is None or self.trace is None:
            raise Exception("Could not load trace or transparent tile images.")

        self.transparent = self.ensure_tile(self.transparent)
        self.trace = self.ensure_tile(self.trace)

    def ensure_tile(self, img):
        # Make sure tile is 4 channels, correct size
        if img.shape[:2] != (self.tile_size, self.tile_size):
            img = cv2.resize(img, (self.tile_size, self.tile_size))
        if img.shape[2] == 3:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
        return img

    def generate_overlay(self, overlayData):
        row_imgs = []
        for row in overlayData:
            tiles = []
            for block in row:
                if block == "trace":
                    tiles.append(self.trace)
                else:
                    tiles.append(self.transparent)
            row_img = cv2.hconcat(tiles)
            row_imgs.append(row_img)
        full_overlay = cv2.vconcat(row_imgs)
        return full_overlay

    def draw_text(self, img, coord, text, color=(0, 255, 0)):
        x = coord[0] * self.tile_size + 30
        y = coord[1] * self.tile_size + 170
        cv2.putText(
            img,
            text,
            (x, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.2,
            color,
            3,
            cv2.LINE_AA,
        )

    def main(self, path):
        base_map = cv2.imread("assets/genMaps/floor_1.png", cv2.IMREAD_UNCHANGED)
        if base_map is None:
            print("Base map not found.")
            return

        h, w = base_map.shape[:2]
        cols = w // self.tile_size
        rows = h // self.tile_size

        overlayData = [["" for _ in range(cols)] for _ in range(rows)]
        for x, y in path:
            overlayData[y][x] = "trace"

        overlay = self.generate_overlay(overlayData)

        # Blend with base map
        base = base_map[:, :, :3]
        alpha = overlay[:, :, 3:] / 255.0
        overlay_rgb = overlay[:, :, :3]
        result = (alpha * overlay_rgb + (1 - alpha) * base).astype(np.uint8)

        # Draw Start and End
        if path:
            self.draw_text(result, path[0], "START", (0, 255, 0))
            self.draw_text(result, path[-1], "END", (0, 0, 255))

        cv2.imwrite("assets/genMaps/map.png", result)


class PathFind:

    def __init__(self):
        with open("assets/db/floor_1.txt", "r") as f:
            input_str = f.read()
        self.pathMatrix = [
            line.strip().split(" ") for line in input_str.strip().split("\n")
        ]

    def getBlock(self, coords):
        try:
            return self.pathMatrix[coords[1]][coords[0]]
        except IndexError:
            return None

    def getCoords(self, room):
        room = room.lower()
        for y, row in enumerate(self.pathMatrix):
            for x, val in enumerate(row):
                if val.lower() == room:
                    return (x, y)
        return None

    def getNeighbors(self, x, y):
        directions = [(0, -1), (-1, 0), (1, 0), (0, 1)]
        neighbors = []
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if self.getBlock((nx, ny)) == "path":
                neighbors.append((nx, ny))
        return neighbors

    def findPath(self, start, end):
        start = self.getCoords(start) if isinstance(start, str) else start
        end = self.getCoords(end) if isinstance(end, str) else end
        if not start or not end:
            print("Invalid start or end.")
            return []

        # Find walkable neighbors of start and end
        start_paths = [n for n in self.getNeighbors(*start)]
        end_paths = [n for n in self.getNeighbors(*end)]

        if not start_paths or not end_paths:
            print("Start or end not adjacent to path.")
            return []

        queue = deque()
        visited = set()
        prev = {}

        for s in start_paths:
            queue.append(s)
            visited.add(s)
            prev[s] = start  # link to starting room

        target = None

        while queue:
            current = queue.popleft()
            if current in end_paths:
                target = current
                break
            for neighbor in self.getNeighbors(*current):
                if neighbor not in visited:
                    visited.add(neighbor)
                    prev[neighbor] = current
                    queue.append(neighbor)

        if not target:
            print("Path not found")
            return []

        # Reconstruct path
        path = []
        at = target
        while at != start:
            path.append(at)
            at = prev.get(at)
            if at is None:
                print("Path reconstruction failed")
                return []
        path.append(start)
        path.reverse()
        return path


class GenMap:

    empty = cv2.imread("assets/mapComp/empty.png")
    lift = cv2.imread("assets/mapComp/lift.png")
    stairs = cv2.imread("assets/mapComp/stairs.png")
    path = cv2.imread("assets/mapComp/path.png")

    def genRoom(self, text, fontSize=65):
        template = Image.open("assets/mapComp/room.png")
        font = ImageFont.truetype("FreeMono.ttf", fontSize)
        ImageDraw.Draw(template).text((70, 110), text, fill=(0, 0, 0), font=font)
        template.save("assets/genMaps/temp/room.png")
        return cv2.imread("assets/genMaps/temp/room.png")

    def genRow(self, row):
        newRow = []
        for block in row:
            if block.lower() == "empty":
                newRow.append(GenMap.empty)
            if block.lower() == "lift":
                newRow.append(GenMap.lift)
            if block.lower() == "stairs":
                newRow.append(GenMap.stairs)
            if block.lower() == "path":
                newRow.append(GenMap.path)
            if block.lower() not in ["empty", "lift", "stairs", "path"]:
                newRow.append(self.genRoom(str(block).upper()))
        rowImage = cv2.hconcat(newRow)
        return rowImage

    def genCol(self, col):
        colImage = cv2.vconcat(col)
        return colImage

    def genMap(self, mapData, mapName="map"):
        rows = []
        for row in mapData:
            rows.append(self.genRow(row))
        columns = self.genCol(rows)
        cv2.imwrite(f"assets/genMaps/{mapName}.png", columns)


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
        # if len(roomNum) > 3:
        #     return True
        # else:
        #     return False

        roomNum = roomNum.upper()

        validpattern1 = re.compile(r"[A-Z]\d{3}")
        validpattern2 = re.compile(r"[A-Z]\d{3}[A-Z]")

        def sanitize(roomNum):
            roomNum = roomNum.replace(" ", "").replace("-", "")
            return roomNum

        def valid(roomNum):
            roomNum = sanitize(roomNum)
            if validpattern1.fullmatch(roomNum) or validpattern2.fullmatch(roomNum):
                return True
            else:
                return False

        def valid_r(n):
            n = sanitize(n)
            validpattern1 = re.compile(r"[SNA][0-4][0-1][0-9]")
            validpattern2 = re.compile(r"[SNA][0-4][0-1][0-9][A-E]")
            if validpattern1.search(n) or validpattern2.search(n) or n == "SCC":
                return True
            else:
                return False

        return valid_r(roomNum)


def delayedPathPage(app):
    app.page.views.pop()
    app.page.views.append(Pages.pathPage(app))
    app.page.update()


def zoomable_image(img):
    return ft.GestureDetector(
        content=ft.Container(
            content=ft.InteractiveViewer(
                content=img,
                scale_enabled=True,
                pan_enabled=True,
                boundary_margin=100,
                min_scale=0.5,
                max_scale=4,
            )
        ),
        on_scale_start=lambda e: None,
        on_scale_update=lambda e: None,
        on_scale_end=lambda e: None,
    )


class Pages:

    fromRoomNumber = None
    toRoomNumber = None

    mapImage = zoomable_image(
        ft.Image(
            src="assets/genMaps/floor_1.png",
            fit=ft.ImageFit.FILL,
        )
    )

    pathTraceImage = zoomable_image(
        ft.Image(
            src="assets/genMaps/map.png",
            fit=ft.ImageFit.FILL,
        )
    )

    def updateMapSize(app, width, height):
        Pages.mapImage.width = width
        Pages.mapImage.height = height - 80
        Pages.pathTraceImage.width = width
        Pages.pathTraceImage.height = height - 80

    def loadingPage(app):
        return ft.View(
            "/loading",
            [
                ft.AppBar(title=ft.Text("Loading Path"), center_title=True),
                ft.Container(
                    content=ft.ProgressRing(),
                    alignment=ft.alignment.center,
                    expand=True,
                ),
            ],
        )

    def homePage(app):
        return ft.View(
            "/homePage",
            [
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                "GAIA Navigator", size=60, weight=ft.FontWeight.BOLD
                            ),
                            ft.Text("Navigate your college effortlessly", size=20),
                            ft.Container(height=40),
                            ft.ElevatedButton(
                                # icon=ft.icons.MAP,
                                text="Navigate",
                                icon_color="white",
                                on_click=lambda _: app.page.go("/fromInputPage"),
                                style=ft.ButtonStyle(
                                    padding=20,
                                    shape=ft.RoundedRectangleBorder(radius=20),
                                    elevation=10,
                                ),
                            ),
                            ft.ElevatedButton(
                                # icon=ft.icons.BUILD,
                                text="Generate Maps",
                                icon_color="white",
                                on_click=lambda _: app.page.go("/mapGenPage"),
                                style=ft.ButtonStyle(
                                    padding=20,
                                    shape=ft.RoundedRectangleBorder(radius=20),
                                    elevation=10,
                                ),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=20,
                    ),
                    alignment=ft.alignment.center,
                    expand=True,
                ),
            ],
        )

    def fromInputPage(app):
        mapImage = Pages.mapImage
        Pages.updateMapSize(app, app.page.width, app.page.height)

        def getRoomNum(e):
            global fromRoomNumber
            fromRoomNumber = fromRoomInput.value
            if Functions.roomNumberIsValid(fromRoomNumber):
                app.page.go("/toInputPage")
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
            border_radius=20,
            text_size=15,
            bgcolor=ft.colors.BACKGROUND,
            border_width=0.3,
            height=43,
        )

        return ft.View(
            "/fromInputPage",
            [
                ft.AppBar(
                    title=ft.Text("From"),
                    bgcolor=ft.colors.SURFACE_VARIANT,
                    center_title=True,
                ),
                ft.Container(
                    ft.Stack(
                        [
                            mapImage,
                            ft.Container(
                                content=ft.Row(
                                    [
                                        fromRoomInput,
                                        # ft.ElevatedButton("Next", on_click=getRoomNum),
                                    ],
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    spacing=10,
                                ),
                                alignment=ft.alignment.center,
                            ),
                        ]
                    ),
                ),
                notValidInputWarning,
                # ft.ElevatedButton("Next", on_click=getRoomNum),
            ],
        )

    def toInputPage(app):
        mapImage = Pages.mapImage
        Pages.updateMapSize(app, app.page.width, app.page.height)

        def getRoomNum(e):
            global toRoomNumber
            toRoomNumber = toRoomInput.value
            if Functions.roomNumberIsValid(toRoomNumber):
                app.page.go("/loadingPage")
                threading.Thread(target=lambda: delayedPathPage(app)).start()
            else:
                notValidInputWarning.open = True
                app.page.update()

        notValidInputWarning = ft.SnackBar(
            content=ft.Text("Please enter a valid Room Number!"), action="Got it!"
        )

        toRoomInput = ft.TextField(
            label="To",
            hint_text="Enter Room Number",
            on_submit=getRoomNum,
            border_radius=20,
            text_size=15,
            bgcolor=ft.colors.BACKGROUND,
            border_width=0.3,
            autofocus=True,
            height=43,
        )

        return ft.View(
            "/toInputPage",
            [
                ft.AppBar(
                    title=ft.Text("To"),
                    bgcolor=ft.colors.SURFACE_VARIANT,
                    center_title=True,
                ),
                ft.Container(
                    ft.Stack(
                        [
                            mapImage,
                            ft.Container(
                                content=ft.Row(
                                    [
                                        toRoomInput,
                                        # ft.ElevatedButton("Next", on_click=getRoomNum),
                                    ],
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    spacing=10,
                                ),
                                alignment=ft.alignment.center,
                            ),
                        ]
                    ),
                ),
                notValidInputWarning,
                # ft.ElevatedButton("Next", on_click=getRoomNum),
            ],
        )

    def pathPage(app):
        global fromRoomNumber, toRoomNumber

        finder = PathFind()
        path = finder.findPath(fromRoomNumber, toRoomNumber)
        debug(path)

        tracer = TracePath()
        tracer.main(path)

        Pages.updateMapSize(app, app.page.width, app.page.height)

        return ft.View(
            "/pathPage",
            [
                ft.AppBar(title=ft.Text("Path"), center_title=True),
                ft.Container(
                    ft.Stack(
                        [
                            zoomable_image(Pages.mapImage),
                            zoomable_image(Pages.pathTraceImage),
                        ]
                    ),
                    expand=True,
                ),
            ],
        )

    def mapGenPage(app):

        mapDataInput = ft.TextField(
            label="Map Data",
            hint_text="Enter Map Data",
            multiline=True,
            max_lines=10,
            border_radius=20,
            text_size=15,
            bgcolor=ft.colors.BACKGROUND,
            border_width=0.3,
        )

        def loadDB(e):
            file_picker.pick_files(allow_multiple=False)

        def fileSelected(e):
            if e.files:
                file_path = e.files[0].path
                with open(file_path, "r") as f:
                    mapDataInput.value = f.read()
                app.page.update()

        def generate(e):
            MapGenerator = GenMap()
            mapData = [row.split() for row in mapDataInput.value.strip().split("\n")]
            mapName = mapNameInput.value.replace(" ", "_")
            MapGenerator.genMap(mapData, mapName)
            app.page.snack_bar = ft.SnackBar(
                content=ft.Text("Map generated successfully!")
            )
            app.page.snack_bar.open = True
            app.page.update()

        file_picker = ft.FilePicker(on_result=fileSelected)
        app.page.overlay.append(file_picker)

        mapNameInput = ft.TextField(
            label="Map Name",
            hint_text="Enter Map Name",
            border_radius=20,
            text_size=15,
            bgcolor=ft.colors.BACKGROUND,
            border_width=0.3,
            autofocus=True,
        )

        return ft.View(
            "/mapGenPage",
            [
                ft.AppBar(
                    title=ft.Text("Generate Map"),
                    bgcolor=ft.colors.SURFACE_VARIANT,
                    center_title=True,
                ),
                ft.Container(
                    content=ft.Column(
                        [
                            mapNameInput,
                            mapDataInput,
                            ft.Row(
                                [
                                    ft.ElevatedButton("Load DB File", on_click=loadDB),
                                    ft.ElevatedButton(
                                        "Generate Map", on_click=generate
                                    ),
                                ],
                                spacing=10,
                            ),
                        ],
                        expand=True,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        alignment=ft.MainAxisAlignment.START,
                    ),
                    padding=20,
                ),
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

    flag = True

    def route_change(self, route):
        if self.flag == True:
            self.page.views.clear()
            self.page.views.append(Pages.homePage(self))
            self.flag = False
        if self.page.route == "/fromInputPage":
            self.page.views.append(Pages.fromInputPage(self))
        if self.page.route == "/toInputPage":
            self.page.views.pop()
            self.page.views.append(Pages.toInputPage(self))
        if self.page.route == "/pathPage":
            self.page.views.pop()
            self.page.views.append(Pages.pathPage(self))
        if self.page.route == "/mapGenPage":
            self.page.views.append(Pages.mapGenPage(self))
        if self.page.route == "/loadingPage":
            self.page.views.append(Pages.loadingPage(self))
        debug(self.page.views)
        self.page.update()

    def pageResize(self, event):
        Pages.updateMapSize(self, self.page.window_width, self.page.window_height)
        self.page.go(self.page.views[-1].route)

    def main(self):
        self.page.on_resize = self.pageResize
        self.page.on_route_change = self.route_change
        self.page.on_view_pop = self.view_pop
        self.page.go(self.page.route)


ft.app(target=Main)
