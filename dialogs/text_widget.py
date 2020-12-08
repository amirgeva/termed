from dialogs.widget import Widget
from geom import Point
from utils import fit_text


class TextWidget(Widget):
    def __init__(self, win):
        super().__init__(win)
        self.text = ''
        self.editable = False
        self.offset = 0
        self.cursor = 0

    def set_text(self, text):
        self.text = text
        self.cursor = len(self.text)
        self.scroll()
        self.speak('modified')

    def scroll(self):
        p = self.cursor - self.offset
        if p < 0 or p > self.window.width():
            self.offset = self.cursor - self.window.width() // 2

    def set_editable(self, state):
        self.editable = state
        self.cursor_on = state

    def process_key(self, key):
        if self.editable:
            self.set_text(self.text + key)

    def backspace(self, flags):
        if self.editable and len(self.text) > 0:
            self.set_text(self.text[0:-1])

    def render(self):
        super().render()
        self.window.set_cursor(Point(0, 0))
        text = fit_text(self.text, self.window.width())
        self.window.text(text)
        self.window.set_cursor(Point(self.cursor - self.offset,0))
