from config import get_app
from focus import FocusTarget


class Widget(FocusTarget):
    def __init__(self, win):
        super().__init__()
        self._window = win
        self._parent = None
        self._cursor_on = False
        self._signals = {}
        self._tab_stop = False

    def __bool__(self):
        return self._window is not None

    def is_tab_stop(self):
        return self._tab_stop

    def listen(self, signal: str, callback: callable):
        if signal not in self._signals:
            self._signals[signal] = []
        self._signals[signal].append(callback)
        return self

    def speak(self, signal):
        if signal in self._signals:
            listeners = self._signals.get(signal)
            for callback in listeners:
                callback()
        return self

    def disable_border(self):
        if self._window:
            self._window.disable_border()
        return self

    def set_parent(self, parent):
        self._parent = parent
        return self

    def set_title(self, title):
        self._window.set_title(title)
        return self

    def on_focus(self):
        get_app().cursor(self._cursor_on)
        return self

    def on_leave_focus(self):
        return self

    def is_focus(self):
        if self._parent is None:
            return True
        if not hasattr(self._parent, 'focus'):
            return False
        return self is self._parent.focus

    def render(self):
        self._window.render()
        return self
