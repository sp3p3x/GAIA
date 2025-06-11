import time, cv2, re
import flet as ft
from PIL import Image, ImageDraw, ImageFont


DEBUG = True


def debug(data):
    if DEBUG:
        print(f"{time.strftime('%H:%M:%S', time.gmtime())}: {data}\n")


class TracePath:

    transparent = cv2.imread("assets/mapComp/transparent.png", cv2.IMREAD_UNCHANGED)
    trace = cv2.imread("assets/mapComp/trace.png", cv2.IMREAD_UNCHANGED)

    def genRow(self, row):
        newRow = []
        for block in row:
            if block.lower() == "transparent":
                newRow.append(TracePath.transparent)
            if block.lower() == "trace":
                newRow.append(TracePath.trace)
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
        # rows = []
        # for row in mapData:
        #     row_img = self.genRow(row)
        #     if row_img is not None:
        #         rows.append(row_img)

        # if not rows:
        #     print("No valid rows generated")
        #     return

        # columns = cv2.vconcat(rows)
        # cv2.imwrite(f"assets/genMaps/{mapName}.png", columns)

    def generate(self, data):
        MapGenerator = TracePath()
        mapName = "map".replace(" ", "_")
        MapGenerator.genMap(data, mapName)

    def main(self, path):
        blockSize = 300
        mapPath = cv2.imread("assets/genMaps/ground_floor.png")
        mapSize = [mapPath.shape[1], mapPath.shape[0]]

        rows = int(mapSize[0] / 300)
        cols = int(mapSize[1] / 300)
        data = ((((" transparent " * rows).strip()) + "\n") * cols).strip()

        mapData = []
        rows = data.split("\n")
        for row in rows:
            mapData.append(row.split())

        debug(path)
        path = [[4, 3], [4, 2], [4, 1], [3, 1], [2, 1], [2, 2]]

        for i in path:
            mapData[i[1]][i[0]] = "trace"

        self.generate(mapData)


class PathFind:
    inputStr = """empty empty empty empty empty empty empty
    empty n102 path path path scc empty
    empty n011 path empty path s011 empty
    empty n001 path empty path s011 empty"""

    # with open("assets/db/floor_1.txt", "r") as f:
    #     inputStr = f.read()

    pathMatrix = [i.split(" ") for i in inputStr.split("\n")]

    traversedPath = []
    pathFound = False

    def getBlock(self, coords):
        try:
            room = self.pathMatrix[coords[1]][coords[0]]
        except:
            return False
        return room

    def getCoords(self, room):
        coords = None
        for i in range(len(self.pathMatrix)):
            try:
                if self.pathMatrix[i].index(room):
                    coords = (self.pathMatrix[i].index(room), i)
            except:
                pass
        return coords

    def getSurrounding(self, coords):
        x = coords[0]
        y = coords[1]

        foobar = [
            [x, y - 1, self.getBlock([x, y - 1])],
            [x - 1, y, self.getBlock([x - 1, y])],
            [x + 1, y, self.getBlock([x + 1, y])],
            [x, y + 1, self.getBlock([x, y + 1])],
        ]

        surroundCoords = []

        for block in foobar:
            if block[2] != False:
                surroundCoords.append(block)

        return surroundCoords

    def recurse(self, start, end):
        global pathFound, traversedPath

        queue = []

        if type(start) == str:
            startCoords = self.getCoords(start)
        else:
            startCoords = start

        for block in self.getSurrounding(startCoords):
            if block[2] != end:
                if block[2] == "path":
                    foo = [block[0], block[1]]
                    if foo not in self.traversedPath and not self.pathFound:
                        self.traversedPath.append(foo)
                        queue.append(foo)
                        self.recurse(queue[0], end)
                        queue.pop()
                if "path" not in self.getSurrounding(startCoords):
                    pass
            else:
                self.pathFound = True

    def findPath(self, start, end):
        global traversedPath, pathFound

        self.recurse(start, end)

        if self.pathFound:
            path = self.traversedPath
        else:
            print("Cannot find path!")

        self.traversedPath = []
        self.pathFound = False

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


class Pages:

    fromRoomNumber = None
    toRoomNumber = None

    mapImage = ft.Image(
        src="assets/genMaps/ground_floor.png",
        fit=ft.ImageFit.FILL,
    )

    pathTraceImage = ft.Image(
        src="assets/genMaps/map.png",
        fit=ft.ImageFit.FILL,
    )

    def updateMapSize(app, width, height):
        Pages.mapImage.width = width
        Pages.mapImage.height = height - 80
        Pages.pathTraceImage.width = width
        Pages.pathTraceImage.height = height - 80

    def homePage(app):
        return ft.View(
            "/homePage",
            [
                # ft.AppBar(title=ft.Text("Main Menu"),bgcolor=ft.colors.SURFACE_VARIANT,center_title=True),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.ElevatedButton(
                                content=ft.Text("Navigate", size=60),
                                on_click=lambda _: app.page.go("/fromInputPage"),
                            ),
                            ft.ElevatedButton(
                                content=ft.Text("Generate Maps", size=60),
                                on_click=lambda _: app.page.go("/mapGenPage"),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=30,
                    ),
                    alignment=ft.alignment.center,
                    padding=100,
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
                app.page.go("/pathPage")
            else:
                notValidInputWarning.open = True
                app.page.update()
                debug("input insufficient")

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
        global fromRoomNumber
        global toRoomNumber

        finder = PathFind()
        path = finder.findPath(fromRoomNumber, toRoomNumber)
        debug(path)

        tracer = TracePath()
        tracer.main(path)

        mapImage = Pages.mapImage
        Pages.updateMapSize(app, app.page.width, app.page.height)

        pathTraceImage = Pages.pathTraceImage
        Pages.updateMapSize(app, app.page.width, app.page.height)

        return ft.View(
            "/pathPage",
            [
                ft.AppBar(
                    title=ft.Text("Path"),
                    bgcolor=ft.colors.SURFACE_VARIANT,
                    center_title=True,
                ),
                ft.Container(
                    ft.Stack(
                        [
                            mapImage,
                            pathTraceImage,
                            ft.Container(
                                content=ft.Row(
                                    [],
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    spacing=10,
                                ),
                                alignment=ft.alignment.center,
                            ),
                        ]
                    ),
                ),
            ],
        )

    def mapGenPage(app):

        def generate(e):
            MapGenerator = GenMap()
            mapData = []
            rows = mapDataInput.value.split("\n")
            for row in rows:
                mapData.append(row.split())
            mapName = mapNameInput.value.replace(" ", "_")
            MapGenerator.genMap(mapData, mapName)

        mapNameInput = ft.TextField(
            label="Map Name",
            hint_text="Enter Map Name",
            border_radius=20,
            text_size=15,
            bgcolor=ft.colors.BACKGROUND,
            border_width=0.3,
            autofocus=True,
        )

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

        return ft.View(
            "/mapGenPage",
            [
                ft.AppBar(
                    title=ft.Text("Generate Map"),
                    bgcolor=ft.colors.SURFACE_VARIANT,
                    center_title=True,
                ),
                mapNameInput,
                mapDataInput,
                ft.ElevatedButton("Generate Map", on_click=generate),
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
