from line import Line
from geom import Point


class Document:
    def __init__(self, filename):
        self._lines = [Line('')]
        self._modified = False
        if filename:
            self.load(filename)

    def load(self, filename):
        try:
            lines = open(filename).readlines()
            self._lines = [Line(s.rstrip()) for s in lines]
        except OSError:
            return False
        return True

    def size(self):
        return len(self._lines)

    def rows_count(self):
        return len(self._lines)

    def get_row(self, y):
        return self._lines[y]

    def __getitem__(self, item):
        return self._lines[item]

    def join_next_row(self, row_index):
        if 0 <= row_index < (self.rows_count() - 1):
            row = self.get_row(row_index)
            next_row = self.get_row(row_index + 1)
            del self._lines[row_index + 1]
            self._lines[row_index].set_text(row.get_text() + next_row.get_text())
            # if not self.undoing:
            #    self.undos.append([self.new_line, Point(len(row), row_index)])
            self._modified = True

    def delete_line(self, index):
        if 0 <= index < len(self._lines):
            self._modified = True
            del self._lines[index]

    def delete_block(self, y, x0, x1):
        self._modified = True
        line = self.get_row(y)
        line.delete_block(x0, x1)

    def insert(self, line, at):
        self._modified = True
        self._lines.insert(at, line)

    def set_cursor(self, cursor):
        if cursor.y < 0:
            return Point(0, 0)
        if cursor.y >= self.rows_count():
            return Point(0, self.rows_count() - 1)
        row = self.get_row(cursor.y)
        x = cursor.x
        if x < 0:
            x = 0
        if x > len(row):
            x = len(row)
        return Point(x, cursor.y)

    def add_char(self, c, cursor, insert):
        line = self._lines[cursor.y]
        if not insert and cursor.x < len(line):
            line.delete_char(cursor.x)
        line.insert_char(cursor.x, c)
        # if not self.undoing:
        #     self.undos.append([self.delete_char, Point(cursor)])
        # self.invalidate()
        self._modified = True
        return Point(1, 0)
