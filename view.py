from typing import List
from cursor import Cursor
# from line import Line
from text_token import Token
import config
from geom import Point, Range
from focus import FocusTarget
import pyperclip


# noinspection PyTypeChecker
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
            last: Token = None
            x = 0
            for k in range(line.get_token_count()):
                t = line.get_token(k)
                if t.get_text_index() <= c.x <= (t.get_text_index() + len(t.get_text())):
                    x = t.get_visual_index() + (c.x - t.get_text_index())
                    break
                if c.x < t.get_text_index():
                    x = t.get_visual_index()
                    for i in range(t.get_text_index() - c.x):
                        x = x - config.const.TABSIZE
                        if last and x <= (last.get_visual_index() + len(last.get_text())):
                            x = last.get_visual_index() + len(last.get_text())
                            break
                    break
                last = t
            return x, y
        return 0, 0

    def insert_text(self, full_text):
        text_lines = full_text.split('\n')
        first = True
        for text in text_lines:
            if not first:
                self.action_enter()
            line = self.doc[self.cursor.y]
            if self.cursor.x >= line.size():
                line.append_text(text)
            else:
                line.insert_text(self.cursor.x, text)
            self.cursor.move(len(text), 0)
            first = False
        self.draw_cursor_line()
        self.place_cursor()

    def action_backtab(self):
        if self.selection is not None:
            y0 = self.selection.start.y
            if self.selection.start.x >= self.doc[y0].size():
                y0 = y0 + 1
            y1 = self.selection.stop.y
            if self.selection.stop.x == 0:
                y1 = y1 - 1
            while y0 <= y1:
                line = self.doc[y0]
                if line.get_text().startswith('\t'):
                    line.set_text(line.get_text()[1:])
                y0 = y0 + 1

    def action_tab(self):
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
        if self.cursor.x < line.size():
            line.delete_char(self.cursor.x)
            self.draw_cursor_line()
        elif self.cursor.y < (self.doc.size() - 1):
            next_line = self.doc[self.cursor.y + 1]
            line.join(next_line)
            self.doc.delete_line(self.cursor.y + 1)
            self.redraw_all()

    def action_backspace(self):
        if self.selection is not None:
            self.delete_selection()
            return
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
            if token.get_visual_index() > visual:
                n = token.get_visual_index() - visual
                t = Token(' ' * n, visual, text_index)
                t._blank = True
                tokens.insert(idx, t)
                visual = token.get_visual_index()
                text_index = token.get_text_index()
            else:
                text_index += len(token.get_text())
                visual += len(token.get_text())
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
                    to_i = tokens[-1].get_text_index() + len(tokens[-1].get_text())
                else:
                    to_i = stop.x
                i = 0
                while i < len(tokens):
                    token = tokens[i]
                    t_start = token.get_text_index()
                    t_stop = token.get_text_index() + len(token.get_text())
                    if from_i <= t_start and to_i >= t_stop:
                        token.set_color(sel_highlight)
                        i = i + 1
                    elif from_i >= t_stop or to_i <= t_start:
                        i = i + 1
                    elif from_i > t_start:
                        n = from_i - t_start
                        next_token = token.get_right_part(n)
                        next_token.set_color(1)
                        token.set_text(token.get_text()[0:n])
                        tokens.insert(i + 1, next_token)
                        i = i + 1
                    else:
                        n = to_i - t_start
                        next_token = token.get_right_part(n)
                        next_token.set_color(token.get_color())
                        token.set_text(token.get_text()[0:n])
                        token.set_color(sel_highlight)
                        tokens.insert(i + 1, next_token)
                        i = i + 1

    def clamp_tokens(self, tokens: List[Token]):
        i = 0
        while i < len(tokens):
            t = tokens[i]
            if t.get_visual_index() >= self.width() or (t.get_visual_index() + len(t)) <= 0:
                del tokens[i]
            else:
                if t.get_visual_index() < 0:
                    t.set_text(t.get_text()[-t.get_visual_index():])
                    t.set_visual_index(0)
                if (t.get_visual_index() + len(t)) > self.width():
                    t.set_text(t.get_text()[0:(self.width() - t.get_visual_index() - len(t))])
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
        tokens = [line.get_token(i) for i in range(line.get_token_count())]
        self.fill_blanks(tokens, self.window.width())
        self.add_highlights(y, tokens)
        tokens = [t.move(-self.visual_offset.x) for t in tokens]
        self.clamp_tokens(tokens)
        cx = 0
        for token in tokens:
            self.window.set_cursor(token.get_visual_index(), y)
            self.window.set_color(token.get_color())
            self.window.text(token.get_text())
            cx = cx + len(token.get_text())
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

    def get_selection_text(self):
        if self.selection is None:
            return ''
        start, stop = self.selection.get_ordered()
        x = start.x
        lines = []
        for y in range(start.y, stop.y):
            line = self.doc[y]
            lines.append(line.get_text()[x:])
            x = 0
        if stop.x > 0:
            line = self.doc[stop.y]
            lines.append(line.get_text()[:stop.x])
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

    def process_text_key(self, key):
        if self.selection is not None:
            self.delete_selection()
        if self.doc.add_char(key, self.cursor, self.insert):
            self.action_move_right()

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

    def action_move_left(self):
        self.process_movement((-1, 0), 0)

    def action_move_right(self):
        self.process_movement((1, 0), 0)

    def action_move_up(self):
        self.process_movement((0, -1), 0)

    def action_move_down(self):
        self.process_movement((0, 1), 0)

    def action_move_home(self):
        self.process_movement((-self.cursor.x, 0), 0)

    def action_move_end(self):
        if self.doc:
            n = len(self.doc[self.cursor.y])
            self.process_movement((n, 0), 0)

    def action_move_bod(self):
        self.process_movement((-self.cursor.x, -self.cursor.y), 0)

    def action_move_eod(self):
        if self.doc:
            m = self.doc.size() - self.cursor.y
            n = len(self.doc[-1]) - self.cursor.x
            self.process_movement((n, m), 0)

    def action_move_word_left(self):
        pass

    def action_select_left(self):
        self.process_movement((-1, 0), config.SHIFTED)

    def action_select_right(self):
        self.process_movement((1, 0), config.SHIFTED)

    def action_select_up(self):
        self.process_movement((0, -1), config.SHIFTED)

    def action_select_down(self):
        self.process_movement((0, 1), config.SHIFTED)

    def action_select_home(self):
        self.process_movement((-self.cursor.x, 0), config.SHIFTED)

    def action_select_end(self):
        if self.doc:
            n = len(self.doc[self.cursor.y])
            self.process_movement((n, 0), config.SHIFTED)

    def action_select_bod(self):
        self.process_movement((-self.cursor.x, -self.cursor.y), config.SHIFTED)

    def action_select_eod(self):
        if self.doc:
            m = self.doc.size() - self.cursor.y
            n = len(self.doc[-1]) - self.cursor.x
            self.process_movement((n, m), config.SHIFTED)

    def action_copy(self):
        if self.selection is not None:
            text = self.get_selection_text()
            pyperclip.copy(text)

    def action_paste(self):
        if self.selection is not None:
            self.delete_selection()
        text = pyperclip.paste()
        self.insert_text(text)
