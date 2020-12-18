from config import get_app
from focus import FocusTarget


class Widget(FocusTarget):
    def __init__(self, win):
        super().__init__()
        self._window = win
        self._parent = None
        self._cursor_on = False
        self._signals = {}

    def listen(self, signal: str, callback: callable):
        if signal not in self._signals:
            self._signals[signal] = []
        self._signals[signal].append(callback)

    def speak(self, signal):
        if signal in self._signals:
            listeners = self._signals.get(signal)
            for callback in listeners:
                callback()

    def set_parent(self, parent):
        self._parent = parent

    def set_title(self, title):
        self._window.set_title(title)

    def on_focus(self):
        get_app().cursor(self._cursor_on)

    def on_leave_focus(self):
        pass

    def is_focus(self):
        if self._parent is None:
            return True
        if not hasattr(self._parent, 'focus'):
            return False
        return self is self._parent.focus

    def render(self):
        self._window.render()
