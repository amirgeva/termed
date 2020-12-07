from typing import List
from cursor import Cursor
# from line import Line
from text_token import Token
import config
from geom import Point, Range
from focus import FocusTarget


class View(FocusTarget):
    def __init__(self, window, doc=None):
        super().__init__()
        self.window = window
        self.doc = doc
        self.visual_offset = Point(0, 0)
        self.selection = None
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
            c.clamp_x(0, line.size())

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
            last = None
            x = 0
            for t in line.tokens:
                if t.text_index <= c.x <= (t.text_index + len(t.text)):
                    x = t.visual_index + (c.x - t.text_index)
                    break
                if c.x < t.text_index:
                    x = t.visual_index
                    for i in range(t.text_index - c.x):
                        x = x - config.const.TABSIZE
                        if last and x <= (last.visual_index + len(last.text)):
                            x = last.visual_index + len(last.text)
                            break
                    break
                last = t
            return x, y
        return 0, 0

    def insert_text(self, text):
        line = self.doc[self.cursor.y]
        if self.cursor.x >= line.size():
            line.append_text(text)
        else:
            line.insert_text(self.cursor.x, text)
        self.cursor.move(1, 0)
        self.draw_cursor_line()
        self.place_cursor()

    def backtab(self, flags):
        if self.selection is not None:
            y0 = self.selection.start.y
            if self.selection.start.x >= self.doc[y0].size():
                y0 = y0 + 1
            y1 = self.selection.stop.y
            if self.selection.stop.x == 0:
                y1 = y1 - 1
            while y0 <= y1:
                line = self.doc[y0]
                if line.text.startswith('\t'):
                    line.set_text(line.text[1:])
                y0 = y0 + 1

    def tab(self, flags):
        if self.selection is not None:
            y0 = self.selection.start.y
            if self.selection.start.x >= self.doc[y0].size():
                y0 = y0 + 1
            y1 = self.selection.stop.y
            if self.selection.stop.x == 0:
                y1 = y1 - 1
            while y0 <= y1:
                self.doc[y0].insert_text(0, '\t')
                y0 = y0 + 1
        else:
            self.insert_text('\t')

    def enter(self, flags):
        line = self.doc[self.cursor.y]
        line = line.split(self.cursor.x)
        self.doc.insert(line, self.cursor.y + 1)
        self.cursor = Cursor(0, self.cursor.y + 1)
        self.redraw_all()

    def delete(self, flags):
        line = self.doc[self.cursor.y]
        if self.cursor.x < line.size():
            line.delete_char(self.cursor.x)
            self.draw_cursor_line()
        elif self.cursor.y < (self.doc.size() - 1):
            next_line = self.doc[self.cursor.y + 1]
            line.join(next_line)
            self.doc.delete_line(self.cursor.y + 1)
            self.redraw_all()

    def backspace(self, flags):
        line = self.doc[self.cursor.y]
        if self.cursor.x > 0:
            line.delete_char(self.cursor.x - 1)
            self.cursor.move(-1, 0)
            self.draw_cursor_line()
            self.place_cursor()
        elif self.cursor.y > 0:
            prev_line = self.doc[self.cursor.y - 1]
            x = prev_line.size()
            prev_line.join(line)
            self.doc.delete_line(self.cursor.y)
            self.cursor = Cursor(x, self.cursor.y - 1)
            self.redraw_all()

    @staticmethod
    def fill_blanks(tokens: List[Token], width):
        visual = 0
        text_index = 0
        idx = 0
        while idx < len(tokens):
            token = tokens[idx]
            if token.visual_index > visual:
                n = token.visual_index - visual
                t = Token(' ' * n, visual, text_index)
                t.blank = True
                tokens.insert(idx, t)
                visual = token.visual_index
                text_index = token.text_index
            else:
                text_index += len(token.text)
                visual += len(token.text)
            idx = idx + 1
        if text_index < width:
            n = width - text_index
            tokens.append(Token(' ' * n, visual, text_index))

    def add_highlights(self, y, tokens: List[Token]):
        if self.selection:
            start, stop = self.selection.get_ordered()
            sel_highlight = 1
            if start.y <= y <= stop.y:
                if start.y < y:
                    from_i = 0
                else:
                    from_i = start.x
                if stop.y > y:
                    to_i = tokens[-1].text_index + len(tokens[-1].text)
                else:
                    to_i = stop.x
                i = 0
                while i < len(tokens):
                    token = tokens[i]
                    t_start = token.text_index
                    t_stop = token.text_index + len(token.text)
                    if from_i <= t_start and to_i >= t_stop:
                        token.color = sel_highlight
                        i = i + 1
                    elif from_i >= t_stop or to_i <= t_start:
                        i = i + 1
                    elif from_i > t_start:
                        n = from_i - t_start
                        next = Token(token.text[n:], token.visual_index + n, token.text_index + n)
                        next.color = 1
                        token.text = token.text[0:n]
                        tokens.insert(i + 1, next)
                        i = i + 1
                    else:
                        n = to_i - t_start
                        next = Token(token.text[n:], token.visual_index + n, token.text_index + n)
                        next.color = token.color
                        token.text = token.text[0:n]
                        token.color = sel_highlight
                        tokens.insert(i + 1, next)
                        i = i + 1

    def clamp_tokens(self, tokens: List[Token]):
        i = 0
        while i < len(tokens):
            t = tokens[i]
            if t.visual_index >= self.width() or (t.visual_index + len(t.text)) <= 0:
                del tokens[i]
            else:
                if t.visual_index < 0:
                    t.text = t.text[-t.visual_index:]
                    t.visual_index = 0
                if (t.visual_index + len(t.text)) > self.width():
                    t.text = t.text[0:(self.width() - t.visual_index - len(t.text))]
                i = i + 1

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
        tokens = [t.clone() for t in line.tokens]
        self.fill_blanks(tokens, self.window.width())
        self.add_highlights(y, tokens)
        tokens = [t.move(-self.visual_offset.x) for t in tokens]
        self.clamp_tokens(tokens)
        cx = 0
        for token in tokens:
            self.window.set_cursor(token.visual_index, y)
            self.window.set_color(token.color)
            self.window.text(token.text)
            cx = cx + len(token.text)
        if cx < self.width():
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

    def process_text_key(self, key):
        if self.selection is not None:
            self.delete_selection()
        if self.doc.add_char(key, self.cursor, self.insert):
            self.move_right(0)

    def process_key(self, key):
        if len(key) == 1:
            code = ord(key)
            if 32 <= code < 127:
                self.process_text_key(key)

    def process_movement(self, movement, flags):
        shift = (flags & config.SHIFTED) != 0
        if not shift:
            self.selection = None
        else:
            if self.selection is None:
                self.selection = Range(self.cursor, self.cursor)
        movement = Point(movement)
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

    def move_left(self, flags):
        self.process_movement((-1, 0), flags)

    def move_right(self, flags):
        self.process_movement((1, 0), flags)

    def move_up(self, flags):
        self.process_movement((0, -1), flags)

    def move_down(self, flags):
        self.process_movement((0, 1), flags)

    def move_home(self, flags):
        self.process_movement((-self.cursor.x, 0), flags)

    def move_end(self, flags):
        if self.doc:
            n = len(self.doc[self.cursor.y])
            self.process_movement((n, 0), flags)

    def move_bod(self, flags):
        self.process_movement((-self.cursor.x, -self.cursor.y), flags)

    def move_eod(self, flags):
        if self.doc:
            m = self.doc.size() - self.cursor.y
            n = len(self.doc[-1]) - self.cursor.x
            self.process_movement((n, m), flags)

    def move_word_left(self, flags):
        pass
