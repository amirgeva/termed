from dialogs.widget import Widget
from geom import Point
from utils import fit_text


class TextWidget(Widget):
    def __init__(self, win):
        super().__init__(win)
        self._text = ''
        self._editable = False
        self._offset = 0
        self._cursor = 0

    @property
    def text(self):
        return self._text

    def set_text(self, text):
        self._text = text
        self._cursor = len(self._text)
        self.scroll()
        self.speak('modified')
        return self

    def scroll(self):
        p = self._cursor - self._offset
        if p < 0 or p > self._window.width():
            self._offset = self._cursor - self._window.width() // 2

    def set_editable(self, state):
        self._editable = state
        self._cursor_on = state
        self._tab_stop = True
        return self

    def process_key(self, key):
        if self._editable:
            self.set_text(self._text + key)

    def action_enter(self):
        self.speak('enter')

    def action_backspace(self):
        if self._editable and len(self._text) > 0:
            self.set_text(self._text[0:-1])

    def render(self):
        super().render()
        self._window.set_cursor(Point(0, 0))
        text = fit_text(self._text, self._window.width())
        self._window.text(text)
        self._window.set_cursor(Point(self._cursor - self._offset, 0))
