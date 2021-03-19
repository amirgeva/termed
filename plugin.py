from geom import Point
from window import Window
from focus import FocusTarget


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

    def set_title(self, title: str):
        self._window.set_title(title)

    def get_window(self) -> Window:
        return self._window

    def render(self):
        self._window.render()
