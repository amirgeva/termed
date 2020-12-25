from dialogs.widget import Widget
from geom import Point
from utils import center_text
from color import Color


class Button(Widget):
    def __init__(self, win, text='Button'):
        super().__init__(win)
        self._text = text
        self._tab_stop = True

    def render(self):
        super().render()
        self._window.set_cursor(Point(0, 0))
        text = center_text(self._text, self._window.width())
        color = Color.FOCUS if self.is_focus() else Color.TEXT
        self._window.text(text, color)

    def action_enter(self):
        self.speak('clicked')
