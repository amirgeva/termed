from geom import Rect
from config import get_app
from focus import FocusTarget


class Widget(FocusTarget):
    def __init__(self, win):
        super().__init__()
        self.window = win
        self.parent = None
        self.title = None
        self.cursor_on = False
        self.signals = {}

    def listen(self, signal: str, callback: callable):
        if signal not in self.signals:
            self.signals[signal] = []
        self.signals[signal].append(callback)

    def speak(self, signal):
        if signal in self.signals:
            listeners = self.signals.get(signal)
            for callback in listeners:
                callback()

    def set_parent(self, parent):
        self.parent = parent

    def set_title(self, title):
        self.title = title

    def on_focus(self):
        get_app().cursor(self.cursor_on)

    def on_leave_focus(self):
        pass

    def is_focus(self):
        if self.parent is None:
            return True
        if not hasattr(self.parent, 'focus'):
            return False
        return self is self.parent.focus

    def render(self):
        self.window.render()
        if self.title:
            self.window.render_title(self.title)
