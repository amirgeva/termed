from geom import Rect
from focus import FocusTarget
from dialogs.widget import Widget


class Dialog(FocusTarget):
    def __init__(self, win):
        super().__init__()
        self._window = win
        self._widgets = []
        self._focus: Widget
        self._focus = None

    def add_widget(self, w: Widget):
        self._widgets.append(w)
        w.set_parent(self)
        if self._focus is None:
            self._focus = w
            self._focus.on_focus()

    def render(self):
        self._window.clear()
        self._window.render()
        for w in self._widgets:
            if w is not self._focus:
                w.render()
        if self._focus is not None:
            self._focus.render()

    def subwin(self, *args):
        return self._window.subwindow(Rect(*args))

    @property
    def focus(self):
        return self._focus

    def change_focus(self, d):
        if self._focus is None:
            return
        try:
            i = self._widgets.index(self._focus)
            self._focus.on_leave_focus()
            i = (i + d) % len(self._widgets)
            self._focus = self._widgets[i]
            self._focus.on_focus()
        except ValueError:
            pass

    def on_action(self, action):
        func_name = f'action_{action}'
        if self._focus is not None:
            if action == 'tab':
                self.change_focus(1)
            elif action == 'backtab':
                self.change_focus(-1)
            else:
                if hasattr(self._focus, func_name):
                    f = getattr(self._focus, func_name)
                    f()

    def process_key(self, key):
        if self._focus is not None and hasattr(self._focus, 'process_key'):
            self._focus.process_key(key)

    def ll_key(self, key):
        if self._focus is not None and hasattr(self._focus, 'll_key') and key != '\t':
            self._focus.ll_key(key)
