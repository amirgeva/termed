import re
import config
from geom import Point
from plugin import WindowPlugin
from doc import Document
from view import View
from cursor import Cursor


class OutputPlugin(WindowPlugin):
    def __init__(self):
        super().__init__(Point(0, 10))
        self._offset = 0
        self._error_index = 0
        self._doc = Document('', None)
        self._error_pattern = re.compile(r'^([/.\w]+):(\d+):(\d+): error')
        self._view = View(self.get_window(), self._doc)

    def clear(self):
        self._doc.clear()
        self._view.set_cursor(Cursor(0, 0))

    def add_text(self, text: str):
        text = text.split('\n')
        for line in text:
            self._view.insert_text(line)
            self._view.action_enter()
            self._view.action_select_home()
            self._view.delete_selection()
            self._view.render()
            self._window.flush()

    def global_action_next_error(self):
        return self.action_next_error()

    def action_next_error(self):
        source_root = config.work_dir
        while self._error_index < self._doc.rows_count():
            line = self._doc.get_row(self._error_index).get_logical_text()
            self._error_index += 1
            m = re.search(self._error_pattern, line)
            if m:
                try:
                    g = m.groups()
                    path = g[0]
                    row = int(g[1])
                    col = int(g[2])
                    if path.startswith(source_root):
                        config.get_app().open_file(path, row - 1, col - 1)
                except ValueError:
                    pass
                return
        self._error_index = 0

    def render(self):
        self._view.render()

    def on_action(self, action):
        self._view.on_action(action)

    def on_focus(self):
        super().on_focus()
        config.get_app().cursor(True)
