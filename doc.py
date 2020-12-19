import os
from typing import List
from visual_line import VisualLine
from geom import Point
from cursor import Cursor


class Document:
    def __init__(self, filename):
        self._lines: List[VisualLine] = [VisualLine('')]
        self._modified = False
        self._undo_stack = []
        self._undoing = False
        self._path = ''
        if filename:
            self.load(filename)

    def get_filename(self) -> str:
        return os.path.basename(self._path)

    def get_path(self) -> str:
        return self._path

    def load(self, filename):
        try:
            path = os.path.abspath(filename)
            lines = open(path).readlines()
            self._lines = [VisualLine(s.rstrip()) for s in lines]
            self._path = path
        except OSError:
            return False
        return True

    def save(self, path=''):
        if path:
            self._path = path
        if self._path and len(self._lines) > 0 and self._modified:
            with open(self._path, 'w') as f:
                f.write(self._lines[0].get_logical_text())
                for line in self._lines[1:]:
                    f.write('\n')
                    text = line.get_logical_text()
                    if text:
                        f.write(text)
                self.set_modified(False)

    def set_modified(self, state: bool):
        self._modified = state

    def is_modified(self) -> bool:
        return self._modified

    def size(self) -> int:
        return len(self._lines)

    def rows_count(self) -> int:
        return len(self._lines)

    def get_row(self, y: int) -> VisualLine:
        return self._lines[y]

    def insert_text(self, cursor: Cursor, text: str):
        self.set_modified(True)
        line = self.get_row(cursor.y)
        n = line.get_logical_len()
        x = min(cursor.x, n)
        if not self._undoing:
            self._undo_stack.append([self.delete_block, cursor.y, x, x + len(text)])
        line.insert(x, text)

    def split_line(self, cursor: Cursor):
        self.set_modified(True)
        line = self.get_row(cursor.y)
        line = line.split(cursor.x)
        self.insert(line, cursor.y + 1)
        if not self._undoing:
            self._undo_stack.append([self.join_next_row, cursor.y])

    def join_next_row(self, row_index: int):
        if 0 <= row_index < (self.rows_count() - 1):
            row = self.get_row(row_index)
            next_row = self.get_row(row_index + 1)
            del self._lines[row_index + 1]
            if not self._undoing:
                self._undo_stack.append([self.split_line, Cursor(row.get_logical_len(), row_index)])
            row.extend(next_row)
            self.set_modified(True)

    def delete(self, cursor: Cursor):
        line = self.get_row(cursor.y)
        if cursor.x < line.get_logical_len():
            self.set_modified(True)
            if not self._undoing:
                self._undo_stack.append([self.insert_text, cursor, line.get_logical_text()[cursor.x]])
            line.erase(cursor.x)
        elif cursor.y < (self.size() - 1):
            self.set_modified(True)
            self.join_next_row(cursor.y)

    def backspace(self, cursor: Cursor):
        if cursor.x > 0:
            self.set_modified(True)
            cursor.move(-1, 0)
            self.delete(cursor)
        elif cursor.y > 0:
            self.set_modified(True)
            prev_line = self.get_row(cursor.y - 1)
            x = prev_line.get_logical_len()
            self.join_next_row(cursor.y - 1)
            cursor = Cursor(x, cursor.y - 1)
        return cursor

    def delete_line(self, index: int):
        if 0 <= index < len(self._lines):
            self.set_modified(True)
            if not self._undoing:
                self._undo_stack.append([self.insert, self._lines[index], index])
            del self._lines[index]

    def delete_block(self, y: int, x0: int, x1: int):
        self.set_modified(True)
        line = self.get_row(y)
        if x1 < 0:
            raise RuntimeError('Invalid x1 value')
        n = x1 - x0
        x0, n = line.clip_coords(x0, n)
        if n > 0:
            if not self._undoing:
                self._undo_stack.append([self.insert_text, Cursor(x0, y), line.get_logical_text()[x0:(x0 + n)]])
            line.erase(x0, n)

    def insert(self, line: VisualLine, at: int):
        self.set_modified(True)
        self._lines.insert(at, line)

    def set_cursor(self, cursor: Cursor):
        if cursor.y < 0:
            return Point(0, 0)
        if cursor.y >= self.rows_count():
            return Point(0, self.rows_count() - 1)
        row = self.get_row(cursor.y)
        x = cursor.x
        if x < 0:
            x = 0
        if x > row.get_logical_len():
            x = row.get_logical_len()
        return Point(x, cursor.y)

    def replace_text(self, cursor: Cursor, text: str):
        line = self._lines[cursor.y]
        replace_count = min(line.get_logical_len() - cursor.x, len(text))
        self.start_compound()
        self.delete_block(cursor.y, cursor.x, cursor.x + replace_count)
        self.insert_text(cursor, text)
        self.stop_compound()
        self.set_modified(True)

    def start_compound(self):
        if not self._undoing:
            self._undo_stack.append('{')

    def stop_compound(self):
        if not self._undoing:
            self._undo_stack.append('}')

    def undo(self):
        depth = 0
        if len(self._undo_stack) > 0:
            self.set_modified(True)
        self._undoing = True
        res = Point(0, 0)
        while len(self._undo_stack) > 0:
            cmd = self._undo_stack[-1]
            del self._undo_stack[-1]
            if isinstance(cmd, str):
                if cmd == '{':
                    depth += 1
                if cmd == '}':
                    depth -= 1
            else:
                f = cmd[0]
                f(*cmd[1:])
            if depth == 0:
                break
        self._undoing = False
        return res
