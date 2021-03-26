from geom import Point
from window import Window
from focus import FocusTarget
from menus import Menu


class Plugin(FocusTarget):
    def __init__(self):
        super().__init__()

    def activate(self):
        pass

    def deactivate(self):
        pass

    def render(self):
        pass


class WindowPlugin(Plugin):
    def __init__(self, size: Point = Point(0, 5)):
        super().__init__()
        self._window = Window(size)
        self._menu = Menu('')

    def set_menu(self, menu):
        self._menu = menu

    def get_menu(self):
        return self._menu

    def set_title(self, title: str):
        self._window.set_title(title)

    def get_window(self) -> Window:
        return self._window

    def on_focus(self):
        self._window.set_border_type(1)

    def on_leave(self):
        self._window.set_border_type(0)

    def render(self):
        self._window.render()
