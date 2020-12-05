from line import Line
from geom import Point


class Document:
    def __init__(self, filename):
        self.lines = [Line('')]
        self.modified = False
        if filename:
            self.load(filename)

    def load(self, filename):
        try:
            lines = open(filename).readlines()
            self.lines = [Line(s.rstrip()) for s in lines]
        except OSError:
            return False
        return True

    def size(self):
        return len(self.lines)

    def rows_count(self):
        return len(self.lines)

    def get_row(self, y):
        return self.lines[y]

    def __getitem__(self, item):
        return self.lines[item]

    def join_next_row(self, row_index):
        if 0 <= row_index < (self.rows_count() - 1):
            row = self.get_row(row_index)
            next_row = self.get_row(row_index + 1)
            del self.lines[row_index + 1]
            self.lines[row_index].set_text(row.text + next_row.text)
            # if not self.undoing:
            #    self.undos.append([self.new_line, Point(len(row), row_index)])
            self.modified = True

    def delete_line(self, index):
        if 0 <= index < len(self.lines):
            del self.lines[index]

    def delete_block(self, y, x0, x1):
        line = self.get_row(y)
        line.delete_block(x0, x1)

    def insert(self, line, at):
        self.lines.insert(at, line)

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
        line = self.lines[cursor.y]
        if not insert and cursor.x < len(line):
            line.delete_char(cursor.x)
        line.insert_char(cursor.x, c)
        #if not self.undoing:
        #    self.undos.append([self.delete_char, Point(cursor)])
        #self.invalidate()
        self.modified = True
        return Point(1, 0)
