from geom import Point
from window import Window
from focus import FocusTarget
from menus import Menu


class Plugin(FocusTarget):
    def __init__(self):
        super().__init__()

    def shutdown(self):
        pass

    def activate(self):
        pass

    def deactivate(self):
        pass

    def render(self):
        pass

    def on_mouse(self, eid, x, y, button):
        return False


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

    def on_mouse(self, eid, x, y, button):
        rect = self._window.get_rect()
        if rect.contains(Point(x, y)):
            p = Point(x, y) - rect.top_left()
            if self._window.is_border():
                p = p - Point(1, 1)
            if button == 8:
                self.on_double_click(p)
            if button == 4:
                self.on_click(p)
            return True
        return False

    def on_click(self, p: Point):
        pass

    def on_double_click(self, p: Point):
        pass
