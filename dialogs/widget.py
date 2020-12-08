from geom import Rect
from focus import FocusTarget


class Widget(FocusTarget):
    def __init__(self, win):
        super().__init__()
        self.window = win

    def render(self):
        pass
