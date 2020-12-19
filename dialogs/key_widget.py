from dialogs.widget import Widget
from geom import Point
from utils import fit_text


class KeyWidget(Widget):
    def __init__(self, win):
        super().__init__(win)
        self._text = ''
        self._code = False
        self._cursor_on = True
        self._tab_stop = True

    @property
    def text(self):
        if self._code:
            return chr(int(self._text))
        return self._text

    def set_text(self, text, is_code):
        self._text = text
        self._code = is_code
        self.speak('modified')

    def set_text_from_key(self, key):
        text = key
        code = False
        if len(key) == 1:
            text = str(ord(key))
            code = True
        self.set_text(text, code)

    def ll_key(self, key):
        self.set_text_from_key(key)

    def render(self):
        super().render()
        self._window.set_cursor(Point(0, 0))
        text = fit_text(self._text, self._window.width())
        self._window.text(text)
        self._window.set_cursor(Point(0, 0))
