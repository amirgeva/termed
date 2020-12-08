from geom import Rect
from focus import FocusTarget


class Widget(FocusTarget):
    def __init__(self, win):
        super().__init__()
        self.window = win
        self.parent = None

    def set_parent(self, parent):
        self.parent = parent

    def is_focus(self):
        if self.parent is None:
            return True
        if not hasattr(self.parent, 'focus'):
            return False
        return self is self.parent.focus

    def render(self):
        self.window.render()
