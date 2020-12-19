from typing import List
from geom import Rect
from focus import FocusTarget
import functools
from dialogs.widget import Widget
from window import Window
from config import get_app
from dialogs.button import Button


class Dialog(FocusTarget):
    def __init__(self, win):
        super().__init__()
        self._window: Window = win
        self._widgets: List[Widget] = []
        self._focus: Widget = Widget(None)
        self._result: str = ''

    def get_result(self):
        return self._result

    def close(self, result=None):
        if result:
            self._result = result
        get_app().close_modal()
        if result:
            get_app().modal_result(result)

    def add_widget(self, w: Widget):
        self._widgets.append(w)
        w.set_parent(self)
        if not self._focus:
            self._focus = w
            self._focus.on_focus()

    def render(self):
        self._window.clear()
        self._window.render()
        for w in self._widgets:
            if w is not self._focus:
                w.render()
        if self._focus:
            self._focus.render()

    def subwin(self, *args):
        return self._window.subwindow(Rect(*args))

    @property
    def focus(self):
        return self._focus

    def change_focus(self, d):
        if not self._focus:
            return
        try:
            i = self._widgets.index(self._focus)
            self._focus.on_leave_focus()
            while True:
                i = (i + d) % len(self._widgets)
                if self._widgets[i].is_tab_stop():
                    break
            self._focus = self._widgets[i]
            self._focus.on_focus()
        except ValueError:
            pass

    def set_focus(self, w: Widget):
        try:
            self._widgets.index(w)
            if self._focus:
                self._focus.on_leave_focus()
            self._focus = w
            w.on_focus()
        except ValueError:
            pass

    def on_action(self, action):
        func_name = f'action_{action}'
        if self._focus:
            if action == 'tab':
                self.change_focus(1)
            elif action == 'backtab':
                self.change_focus(-1)
            elif action == 'escape':
                self.close()
            else:
                if hasattr(self._focus, func_name):
                    f = getattr(self._focus, func_name)
                    f()

    def process_key(self, key):
        if self._focus and hasattr(self._focus, 'process_key'):
            self._focus.process_key(key)

    def ll_key(self, key):
        if self._focus and hasattr(self._focus, 'll_key') and key != '\t':
            self._focus.ll_key(key)


class FormDialog(Dialog):
    def __init__(self, window: Window, buttons: List[str]):
        super().__init__(window)
        x = 3
        y = window.height() - 2
        self._buttons = []
        for button_text in buttons:
            button = Button(self.subwin(x, y, len(button_text) + 4, 3), button_text)
            button.listen('clicked', functools.partial(self.clicked, button_text))
            self.add_widget(button)
            self._buttons.append(button)
            x += len(button_text) + 6

    def clicked(self, button_text):
        self.close(button_text)
