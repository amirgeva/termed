import os
from typing import List
from visual_line import VisualLine
from geom import Point
from cursor import Cursor


class Compound:
    def __init__(self, start: bool, cursor: Cursor = None):
        self.start = start
        self.cursor = Cursor(cursor.x, cursor.y)


class Document:
    def __init__(self, filename: str, view):
        self._lines: List[VisualLine] = [VisualLine('')]
        self._modified = False
        self._undo_stack = []
        self._undoing = False
        self._path = ''
        self._view = view
        self._modification_callbacks = []
        if filename:
            if not self.load(filename):
                raise IOError()

    def add_modification_callback(self, cb):
        self._modification_callbacks.append(cb)

    def clear(self):
        self._lines = [VisualLine('')]
        self._undo_stack = []
        self._undoing = False
        self._modified = False

    def get_filename(self) -> str:
        return os.path.basename(self._path)

    def get_path(self) -> str:
        return self._path

    def set_view(self, view):
        self._view = view

    def load(self, filename):
        try:
            path = os.path.abspath(filename)
            lines = open(path).readlines()
            self._lines = [VisualLine(s.rstrip()) for s in lines]
            self._path = path
        except OSError:
            return False
        except UnicodeDecodeError:
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

    def mark_modified(self, y: int):
        for cb in self._modification_callbacks:
            cb(self, y)

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

    def get_text(self, rows=False):
        lines = [line.get_logical_text() for line in self._lines]
        if rows:
            return lines
        return '\n'.join(lines)

    def insert_text(self, cursor: Cursor, text: str):
        self.set_modified(True)
        line = self.get_row(cursor.y)
        n = line.get_logical_len()
        x = min(cursor.x, n)
        if not self._undoing:
            self._undo_stack.append([self._view.get_cursor(), self.delete_block, cursor.y, x, x + len(text)])
        line.insert(x, text)
        self.mark_modified(cursor.y)

    def split_line(self, cursor: Cursor):
        self.set_modified(True)
        line = self.get_row(cursor.y)
        line = line.split(cursor.x)
        self.insert(line, cursor.y + 1)
        self.mark_modified(-1)
        if not self._undoing:
            self._undo_stack.append([self._view.get_cursor(), self.join_next_row, cursor.y])

    def join_next_row(self, row_index: int):
        if 0 <= row_index < (self.rows_count() - 1):
            row = self.get_row(row_index)
            next_row = self.get_row(row_index + 1)
            del self._lines[row_index + 1]
            if not self._undoing:
                self._undo_stack.append(
                    [self._view.get_cursor(), self.split_line, Cursor(row.get_logical_len(), row_index)])
            row.extend(next_row)
            self.set_modified(True)
            self.mark_modified(-1)

    def delete(self, cursor: Cursor):
        line = self.get_row(cursor.y)
        if cursor.x < line.get_logical_len():
            self.set_modified(True)
            if not self._undoing:
                self._undo_stack.append(
                    [self._view.get_cursor(), self.insert_text, cursor, line.get_logical_text()[cursor.x]])
            line.erase(cursor.x)
            self.mark_modified(cursor.y)
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
                self._undo_stack.append([self._view.get_cursor(), self.insert, self._lines[index], index])
            del self._lines[index]
            self.mark_modified(-1)

    def delete_block(self, y: int, x0: int, x1: int):
        self.set_modified(True)
        line = self.get_row(y)
        if x1 < 0:
            raise RuntimeError('Invalid x1 value')
        n = x1 - x0
        x0, n = line.clip_coords(x0, n)
        if n > 0:
            if not self._undoing:
                self._undo_stack.append(
                    [self._view.get_cursor(), self.insert_text, Cursor(x0, y), line.get_logical_text()[x0:(x0 + n)]])
            line.erase(x0, n)
            self.mark_modified(y)

    def insert(self, line: VisualLine, at: int):
        self.set_modified(True)
        self._lines.insert(at, line)
        self.mark_modified(-1)

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

    def replace_text(self, cursor: Cursor, text: str, replace_count: int = -1):
        line = self._lines[cursor.y]
        if replace_count < 0:
            replace_count = len(text)
        replace_count = min(line.get_logical_len() - cursor.x, replace_count)
        self.start_compound()
        self.delete_block(cursor.y, cursor.x, cursor.x + replace_count)
        self.insert_text(cursor, text)
        self.stop_compound()
        self.set_modified(True)

    def start_compound(self):
        if not self._undoing:
            self._undo_stack.append(Compound(True, self._view.get_cursor()))

    def stop_compound(self):
        if not self._undoing:
            if len(self._undo_stack) == 0:
                return
            last = self._undo_stack[-1]
            if isinstance(last, Compound) and last.start:
                del self._undo_stack[-1]
            else:
                self._undo_stack.append(Compound(False, self._view.get_cursor()))

    def undo(self):
        depth = 0
        if len(self._undo_stack) > 0:
            self.set_modified(True)
        self._undoing = True
        res = Point(0, 0)
        while len(self._undo_stack) > 0:
            cmd = self._undo_stack[-1]
            del self._undo_stack[-1]
            if isinstance(cmd, Compound):
                depth += 1 if cmd.start else -1
                if cmd.start and depth == 0:
                    self._view.set_cursor(cmd.cursor)
                    break
            else:
                cursor = cmd[0]
                del cmd[0]
                f = cmd[0]
                f(*cmd[1:])
                if self._view and depth == 0:
                    self._view.set_cursor(cursor)
        self._undoing = False
        return res
