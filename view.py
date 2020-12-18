from typing import List
from cursor import Cursor
from visual_token import VisualToken
from visual_line import VisualLine
import config
from geom import Point, Range
from focus import FocusTarget
from window import Window
from doc import Document
import pyperclip


# noinspection PyTypeChecker
class View(FocusTarget):
    def __init__(self, window: Window, doc: Document = None):
        super().__init__()
        self.window = window
        self.doc = doc
        self.visual_offset = Point(0, 0)
        self.selection: Range = None
        self.cursor = Cursor()
        self.last_x = 0
        self.redraw = True
        self.insert = True

    def width(self):
        return self.window.width()

    def height(self):
        return self.window.height()

    def move_a_cursor(self, c: Cursor, dx: int, dy: int):
        if self.doc:
            c.move(dx, dy)
            c.clamp_y(0, self.doc.size())
            line = self.doc[c.y]
            c.clamp_x(0, line.get_logical_len())

    def move_cursor(self, dx: int, dy: int, move_selection: bool):
        if move_selection:
            if self.selection.empty():
                self.selection = Range(self.cursor.clone(), self.cursor.clone())
            self.move_a_cursor(self.selection.stop, dx, dy)
        elif not self.selection.empty():
            self.selection = Range()
        self.move_a_cursor(self.cursor, dx, dy)

    def place_cursor(self):
        self.window.set_cursor(self.doc2win(self.cursor))

    def doc2win(self, c: Cursor):
        if self.doc:
            y = c.y - self.visual_offset.y
            line = self.doc[c.y]
            x = line.get_visual_index(c.x) - self.visual_offset.x
            return x, y
        return 0, 0

    def insert_text(self, full_text: str):
        text_lines = full_text.split('\n')
        first = True
        for text in text_lines:
            if not first:
                self.action_enter()
            line = self.doc[self.cursor.y]
            if self.cursor.x >= line.get_logical_len():
                line.append(text)
            else:
                line.insert(self.cursor.x, text)
            self.cursor.move(len(text), 0)
            first = False
        self.draw_cursor_line()
        self.place_cursor()

    def action_backtab(self):
        if self.selection is not None:
            y0 = self.selection.start.y
            if self.selection.start.x >= self.doc[y0].get_logical_len():
                y0 = y0 + 1
            y1 = self.selection.stop.y
            if self.selection.stop.x == 0:
                y1 = y1 - 1
            while y0 <= y1:
                line = self.doc[y0]
                if line.get_logical_text().startswith('\t'):
                    line.erase(0)
                y0 = y0 + 1

    def action_tab(self):
        if self.selection is not None:
            y0 = self.selection.start.y
            if self.selection.start.x >= self.doc[y0].get_logical_len():
                y0 = y0 + 1
            y1 = self.selection.stop.y
            if self.selection.stop.x == 0:
                y1 = y1 - 1
            while y0 <= y1:
                self.doc[y0].insert(0, '\t')
                y0 = y0 + 1
        else:
            self.insert_text('\t')

    def action_enter(self):
        line = self.doc[self.cursor.y]
        line = line.split(self.cursor.x)
        self.doc.insert(line, self.cursor.y + 1)
        self.cursor = Cursor(0, self.cursor.y + 1)
        self.redraw_all()

    def action_delete(self):
        if self.selection is not None:
            self.delete_selection()
            return
        line = self.doc[self.cursor.y]
        if self.cursor.x < line.get_logical_len():
            line.erase(self.cursor.x)
            self.draw_cursor_line()
        elif self.cursor.y < (self.doc.size() - 1):
            next_line = self.doc[self.cursor.y + 1]
            line.extend(next_line)
            self.doc.delete_line(self.cursor.y + 1)
            self.redraw_all()

    def action_backspace(self):
        if self.selection is not None:
            self.delete_selection()
            return
        line = self.doc[self.cursor.y]
        if self.cursor.x > 0:
            line.erase(self.cursor.x - 1)
            self.cursor.move(-1, 0)
            self.draw_cursor_line()
            self.place_cursor()
        elif self.cursor.y > 0:
            prev_line = self.doc[self.cursor.y - 1]
            x = prev_line.get_logical_len()
            prev_line.extend(line)
            self.doc.delete_line(self.cursor.y)
            self.cursor = Cursor(x, self.cursor.y - 1)
            self.redraw_all()

    def add_highlights(self, y: int, line: VisualLine) -> List[VisualToken]:
        text = line.get_visual_text()
        res = []
        if self.selection:
            start, stop = self.selection.get_ordered()
            sel_highlight = 1
            if start.y <= y <= stop.y:
                from_i = 0 if start.y < y else line.get_visual_index(start.x)
                to_i = len(text) if stop.y > y else line.get_visual_index(stop.x)
                if from_i > 0:
                    res.append(VisualToken(0, text[0:from_i]))
                res.append(VisualToken(from_i, text[from_i:to_i]))
                res[-1].set_color(sel_highlight)
                if to_i < len(text):
                    res.append(VisualToken(to_i, text[to_i:]))
            else:
                res.append(VisualToken(0, text))
        else:
            res.append(VisualToken(0, text))
        return res

    def draw_cursor_line(self):
        self.draw_line(self.cursor.y - self.visual_offset.y)
        x, y = self.doc2win(self.cursor)
        self.window.set_cursor(x, y)

    def draw_line(self, y: int):
        line_index = y + self.visual_offset.y
        if line_index >= self.doc.size():
            self.window.set_color(0)
            self.window.set_cursor(0, y)
            self.window.text(' ' * self.window.width())
            return
        line = self.doc[line_index]
        tokens = self.add_highlights(y, line)
        x0 = self.visual_offset.x
        x1 = x0 + self.window.width()
        for token in tokens:
            token.move(-x0)
            token.clip(x0, x1)
        cx = 0
        for token in tokens:
            text = token.get_text()
            if len(text) > 0:
                self.window.set_cursor(token.get_pos(), y)
                self.window.set_color(token.get_color())
                self.window.text(text)
                cx = cx + len(text)
        if cx < self.width():
            self.window.set_cursor(cx, y)
            self.window.set_color(0)
            self.window.text(' ' * (self.width() - cx))

    def redraw_all(self):
        # self.window.clear()
        for y in range(self.height()):
            self.draw_line(y)
        self.window.set_cursor(self.doc2win(self.cursor))

    def render(self):
        self.window.render()
        self.redraw_all()

    def scroll_display(self):
        x, y = self.doc2win(self.cursor)
        cx, cy = self.window.contains((x, y))
        if not cy:
            self.visual_offset.y = max(0, self.cursor.y - self.window.height() // 2)

    def get_selection_text(self):
        if self.selection is None:
            return ''
        start, stop = self.selection.get_ordered()
        x = start.x
        lines = []
        for y in range(start.y, stop.y):
            line = self.doc[y]
            lines.append(line.get_logical_text()[x:])
            x = 0
        if stop.x > 0:
            line = self.doc[stop.y]
            lines.append(line.get_logical_text()[:stop.x])
        else:
            lines.append('')
        return '\n'.join(lines)

    def delete_selection(self):
        if self.selection is not None:
            # self.doc.start_compound()
            start, stop = self.selection.get_ordered()
            if start.y == stop.y:
                self.doc.delete_block(start.y, start.x, stop.x)
            else:
                self.doc.delete_block(start.y, start.x, -1)
                self.doc.delete_block(stop.y, 0, stop.x)
                for y in range(start.y + 1, stop.y):
                    self.doc.delete_line(start.y + 1)
                self.doc.join_next_row(start.y)
            self.cursor = start
            # self.doc.stop_compound()
        self.selection = None

    def process_text_key(self, key: str):
        if self.selection is not None:
            self.delete_selection()
        if self.doc.add_char(key, self.cursor, self.insert):
            self.action_move_right()

    def process_key(self, key: str):
        if len(key) == 1:
            code = ord(key)
            if 32 <= code < 127:
                self.process_text_key(key)

    def process_movement(self, movement: Point, flags: int):
        shift = (flags & config.SHIFTED) != 0
        if not shift:
            self.selection = None
        else:
            if self.selection is None:
                self.selection = Range(self.cursor, self.cursor)
        new_cursor = self.doc.set_cursor(self.cursor + movement)
        if movement.x != 0:
            self.last_x = new_cursor.x
        else:
            new_cursor = self.doc.set_cursor(Point(self.last_x, new_cursor.y))
        if self.selection is not None:
            self.selection.extend(new_cursor)
            self.redraw = True
        self.cursor = new_cursor
        self.scroll_display()

    def action_move_left(self):
        self.process_movement(Point(-1, 0), 0)

    def action_move_right(self):
        self.process_movement(Point(1, 0), 0)

    def action_move_up(self):
        self.process_movement(Point(0, -1), 0)

    def action_move_down(self):
        self.process_movement(Point(0, 1), 0)

    def action_move_home(self):
        self.process_movement(Point(-self.cursor.x, 0), 0)

    def action_move_end(self):
        if self.doc:
            n = self.doc[self.cursor.y].get_logical_len()
            self.process_movement(Point(n, 0), 0)

    def action_move_bod(self):
        self.process_movement(Point(-self.cursor.x, -self.cursor.y), 0)

    def action_move_eod(self):
        if self.doc:
            m = self.doc.size() - self.cursor.y
            n = self.doc[-1].get_logical_len() - self.cursor.x
            self.process_movement(Point(n, m), 0)

    def action_move_word_left(self):
        pass

    def action_select_left(self):
        self.process_movement(Point(-1, 0), config.SHIFTED)

    def action_select_right(self):
        self.process_movement(Point(1, 0), config.SHIFTED)

    def action_select_up(self):
        self.process_movement(Point(0, -1), config.SHIFTED)

    def action_select_down(self):
        self.process_movement(Point(0, 1), config.SHIFTED)

    def action_select_home(self):
        self.process_movement(Point(-self.cursor.x, 0), config.SHIFTED)

    def action_select_end(self):
        if self.doc:
            n = self.doc[self.cursor.y].get_logical_len()
            self.process_movement(Point(n, 0), config.SHIFTED)

    def action_select_bod(self):
        self.process_movement(Point(-self.cursor.x, -self.cursor.y), config.SHIFTED)

    def action_select_eod(self):
        if self.doc:
            m = self.doc.size() - self.cursor.y
            n = self.doc[-1].get_logical_len() - self.cursor.x
            self.process_movement(Point(n, m), config.SHIFTED)

    def action_copy(self):
        if self.selection is not None:
            text = self.get_selection_text()
            pyperclip.copy(text)

    def action_paste(self):
        if self.selection is not None:
            self.delete_selection()
        text = pyperclip.paste()
        self.insert_text(text)
