from dialogs.widget import Widget
from geom import Point
from utils import center_text


class Button(Widget):
    def __init__(self, win, text='Button'):
        super().__init__(win)
        self._text = text
        self._tab_stop = True

    def render(self):
        super().render()
        self._window.set_cursor(Point(0, 0))
        text = center_text(self._text, self._window.width())
        self._window.set_color(1 if self.is_focus() else 0)
        self._window.text(text)

    def action_enter(self):
        self.speak('clicked')
