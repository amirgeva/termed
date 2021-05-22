import re
import subprocess as sp
import config
from geom import Point
from plugin import WindowPlugin
from logger import logwrite
from doc import Document
from view import View
from cursor import Cursor


class MakerPlugin(WindowPlugin):
    def __init__(self):
        super().__init__(Point(0, 10))
        self._root = config.get_value('root')
        self._offset = 0
        self._error_index = 0
        self._doc = Document('', None)
        self._error_pattern = re.compile(r'^([/.\w]+):(\d+):(\d+): error')
        self._view = View(self.get_window(), self._doc)

    def global_action_make(self):
        return self.action_make()

    def action_make(self):
        logwrite(f'Make in {self._root}')
        self._doc.clear()
        self._view.set_cursor(Cursor(0, 0))
        p = sp.Popen(['make'], stdout=sp.PIPE, stderr=sp.STDOUT, cwd=self._root)
        for line in p.stdout:
            text = line.decode('utf-8').rstrip()
            self._view.insert_text(text)
            self._view.action_enter()
            self._view.render()
            self._window.flush()

    def global_action_next_error(self):
        return self.action_next_error()

    def action_next_error(self):
        source_root = config.get_value('source_root')
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
