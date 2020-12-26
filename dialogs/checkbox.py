from dialogs.widget import Widget
from window import Window
from geom import Point
from color import Color


class CheckboxWidget(Widget):
    def __init__(self, win: Window, on: bool = False):
        super().__init__(win)
        self._on = on
        self._tab_stop = True
        win.disable_border()

    def render(self):
        super().render()
        self._window.set_cursor(Point(0, 0))
        color = Color.FOCUS if self.is_focus() else Color.TEXT
        self._window.text('[', Color.BORDER)
        self._window.text('X' if self._on else ' ', color)
        self._window.text(']', Color.BORDER)

    def get_state(self) -> bool:
        return self._on

    def set_state(self, state: bool):
        self._on = state

    def toggle(self):
        self._on = not self._on
        self.speak('toggled')

    def process_key(self, key: str):
        if key == ' ':
            self.toggle()
