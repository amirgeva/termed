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
        self._window = window
        self._doc = doc
        self._visual_offset = Point(0, 0)
        self._selection: Range = None
        self._cursor = Cursor()
        self._last_x = 0
        self._redraw = True
        self._insert = True
        self._tabs = []

    def open_tab(self, doc: Document):
        self._tabs.append(self._current_doc_settings())
        self._doc = doc
        self._visual_offset = Point(0, 0)
        self._selection = None
        self._cursor = Cursor()

    def switch_tab(self, first: bool = True):
        if len(self._tabs) == 0:
            return
        index = 0 if first else -1
        tab = self._tabs[index]
        del self._tabs[index]
        if first:
            self._tabs.append(self._current_doc_settings(tab))
        else:
            self._tabs.insert(0, self._current_doc_settings(tab))

    def action_close_tab(self):
        if len(self._tabs) > 0:
            if not config.get_app().save_before_close([self._doc]):
                return
            tab = self._tabs[0]
            del self._tabs[0]
            self._current_doc_settings(tab)
        else:
            config.get_app().action_file_exit()

    def get_all_docs(self):
        res = [self._doc]
        for tab in self.tabs:
            res.append(tab.get('_doc'))
        return res

    def _current_doc_settings(self, tab: dict = None):
        tab_fields = ['_doc', '_visual_offset', '_selection', '_cursor']
        res = {}
        for field in tab_fields:
            res[field] = getattr(self, field)
            if tab is not None:
                setattr(self, field, tab.get(field))
        return res

    def get_doc(self) -> Document:
        return self._doc

    def width(self):
        return self._window.width()

    def height(self):
        return self._window.height()

    def move_a_cursor(self, c: Cursor, dx: int, dy: int):
        if self._doc:
            c.move(dx, dy)
            c.clamp_y(0, self._doc.size())
            line = self._doc.get_row(c.y)
            c.clamp_x(0, line.get_logical_len())

    def move_cursor(self, dx: int, dy: int, move_selection: bool):
        if move_selection:
            if self._selection.empty():
                self._selection = Range(self._cursor.clone(), self._cursor.clone())
            self.move_a_cursor(self._selection.stop, dx, dy)
        elif not self._selection.empty():
            self._selection = Range()
        self.move_a_cursor(self._cursor, dx, dy)

    def place_cursor(self):
        self._window.set_cursor(self.doc2win(self._cursor))

    def doc2win(self, c: Cursor):
        if self._doc:
            y = c.y - self._visual_offset.y
            line = self._doc.get_row(c.y)
            x = line.get_visual_index(c.x) - self._visual_offset.x
            return x, y
        return 0, 0

    def insert_text(self, full_text: str):
        text_lines = full_text.split('\n')
        first = True
        for text in text_lines:
            if not first:
                self.action_enter()
            self._doc.insert_text(self._cursor, text)
            self._cursor.move(len(text), 0)
            first = False
        self.draw_cursor_line()
        self.place_cursor()

    def action_backtab(self):
        if self._selection is not None:
            y0 = self._selection.start.y
            if self._selection.start.x >= self._doc.get_row(y0).get_logical_len():
                y0 = y0 + 1
            y1 = self._selection.stop.y
            if self._selection.stop.x == 0:
                y1 = y1 - 1
            while y0 <= y1:
                line = self._doc.get_row(y0)
                if line.get_logical_text().startswith('\t'):
                    self._doc.delete_block(y0, 0, 1)
                y0 = y0 + 1

    def action_tab(self):
        if self._selection is not None:
            y0 = self._selection.start.y
            if self._selection.start.x >= self._doc.get_row(y0).get_logical_len():
                y0 = y0 + 1
            y1 = self._selection.stop.y
            if self._selection.stop.x == 0:
                y1 = y1 - 1
            while y0 <= y1:
                self._doc.insert_text(Cursor(0, y0), '\t')
                y0 = y0 + 1
        else:
            self.insert_text('\t')

    def action_enter(self):
        self._doc.split_line(self._cursor)
        self._cursor = Cursor(0, self._cursor.y + 1)
        self.redraw_all()

    def action_delete(self):
        if not self.delete_selection():
            self._doc.delete(self._cursor)

    def action_backspace(self):
        if not self.delete_selection():
            self._cursor = self._doc.backspace(self._cursor)

    def add_highlights(self, y: int, line: VisualLine) -> List[VisualToken]:
        text = line.get_visual_text()
        res = []
        if self._selection:
            start, stop = self._selection.get_ordered()
            sel_highlight = 1
            if start.y <= y <= stop.y:
                from_i = 0 if start.y < y else line.get_visual_index(start.x)
                to_i = len(text) if stop.y > y else line.get_visual_index(stop.x)
                if from_i > 0:
                    res.append(VisualToken(0, text[0:from_i]))
                res.append(VisualToken(from_i, text[from_i:to_i]))
                res[-1].set_color(sel_highlight)
                res.append(VisualToken(to_i, text[to_i:]))
                if stop.y > y:
                    res[-1].set_color(sel_highlight)
            else:
                res.append(VisualToken(0, text))
        else:
            res.append(VisualToken(0, text))
        return res

    def draw_cursor_line(self):
        self.draw_line(self._cursor.y - self._visual_offset.y)
        x, y = self.doc2win(self._cursor)
        self._window.set_cursor(x, y)

    def draw_line(self, y: int):
        line_index = y + self._visual_offset.y
        if line_index >= self._doc.size():
            self._window.set_color(0)
            self._window.set_cursor(0, y)
            self._window.text(' ' * self._window.width())
            return
        line = self._doc.get_row(line_index)
        tokens = self.add_highlights(line_index, line)
        x0 = self._visual_offset.x
        x1 = x0 + self._window.width()
        for token in tokens:
            token.move(-x0)
            token.clip(x0, x1)
        cx = 0
        for token in tokens:
            text = token.get_text()
            if len(text) > 0:
                self._window.set_cursor(token.get_pos(), y)
                self._window.set_color(token.get_color())
                self._window.text(text)
                cx = cx + len(text)
        if cx < self.width():
            self._window.set_cursor(cx, y)
            color = 0
            if len(tokens) > 0:
                color = tokens[-1].get_color()
            self._window.set_color(color)
            self._window.text(' ' * (self.width() - cx))

    def redraw_all(self):
        # self.window.clear()
        for y in range(self.height()):
            self.draw_line(y)
        self._window.set_cursor(self.doc2win(self._cursor))

    def _render_tabs(self):
        title = self._doc.get_filename() + (' *' if self._doc.is_modified() else '')
        # self._window.set_title(title)
        if self._window.is_border():
            titles = [(title, 2)]
            for tab in self._tabs:
                tab_doc = tab.get('_doc')
                tab_title = tab_doc.get_filename() + (' *' if tab_doc.is_modified() else '')
                titles.append((tab_title, 0))
            x = 2
            i = 0
            while i < len(titles):
                if (x + 3 + len(titles[i][0])) < self._window.width():
                    self._window.draw_top_frame_text(x, titles[i][0], titles[i][1])
                    x += 3 + len(titles[i][0])
                i += 1

    def render(self):
        self._window.set_footnote(0, f'{self._cursor.x + 1},{self._cursor.y + 1}')
        self._window.render()
        self._render_tabs()
        self.redraw_all()

    def scroll_display(self):
        x, y = self.doc2win(self._cursor)
        cx, cy = self._window.contains((x, y))
        if not cy:
            self._visual_offset.y = max(0, self._cursor.y - self._window.height() // 2)

    def get_selection_text(self):
        if self._selection is None:
            return ''
        start, stop = self._selection.get_ordered()
        x = start.x
        lines = []
        for y in range(start.y, stop.y):
            lines.append(self._doc.get_row(y).get_logical_text()[x:])
            x = 0
        if stop.x > 0:
            lines.append(self._doc.get_row(stop.y).get_logical_text()[:stop.x])
        else:
            lines.append('')
        return '\n'.join(lines)

    def delete_selection(self):
        if self._selection is None:
            return False
        self._doc.start_compound()
        start, stop = self._selection.get_ordered()
        if start.y == stop.y:
            self._doc.delete_block(start.y, start.x, stop.x)
        else:
            dstart = 0
            if start.x > 0:
                self._doc.delete_block(start.y, start.x, self._doc.get_row(start.y).get_logical_len())
                dstart = 1
            if stop.x > 0:
                self._doc.delete_block(stop.y, 0, stop.x)
            for y in range(start.y + dstart, stop.y):
                self._doc.delete_line(start.y + dstart)
            if start.x > 0:
                self._doc.join_next_row(start.y)
        self._cursor = start
        self._doc.stop_compound()
        self._selection = None
        return True

    def process_text_key(self, key: str):
        self.delete_selection()
        if self._insert:
            self._doc.insert_text(self._cursor, key)
        else:
            self._doc.replace_text(self._cursor, key)
        self.action_move_right()

    def process_key(self, key: str):
        if len(key) == 1:
            code = ord(key)
            if 32 <= code < 127:
                self.process_text_key(key)

    def process_movement(self, movement: Point, flags: int):
        shift = (flags & config.SHIFTED) != 0
        if not shift:
            self._selection = None
        else:
            if self._selection is None:
                self._selection = Range(self._cursor, self._cursor)
        new_cursor = self._doc.set_cursor(self._cursor + movement)
        if movement.x != 0:
            self._last_x = new_cursor.x
        else:
            new_cursor = self._doc.set_cursor(Point(self._last_x, new_cursor.y))
        if self._selection is not None:
            self._selection.extend(new_cursor)
            self._redraw = True
        self._cursor = new_cursor
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
        self.process_movement(Point(-self._cursor.x, 0), 0)

    def action_move_end(self):
        if self._doc:
            n = self._doc.get_row(self._cursor.y).get_logical_len()
            self.process_movement(Point(n, 0), 0)

    def action_move_pgdn(self):
        self.process_movement(Point(0, self._window.height()), 0)

    def action_move_pgup(self):
        self.process_movement(Point(0, -self._window.height()), 0)

    def action_move_bod(self):
        self.process_movement(Point(-self._cursor.x, -self._cursor.y), 0)

    def action_move_eod(self):
        if self._doc:
            m = self._doc.size() - self._cursor.y
            n = self._doc.get_row(-1).get_logical_len() - self._cursor.x
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
        self.process_movement(Point(-self._cursor.x, 0), config.SHIFTED)

    def action_select_end(self):
        if self._doc:
            n = self._doc.get_row(self._cursor.y).get_logical_len()
            self.process_movement(Point(n, 0), config.SHIFTED)

    def action_select_pgdn(self):
        self.process_movement(Point(0, self._window.height()), config.SHIFTED)

    def action_select_pgup(self):
        self.process_movement(Point(0, -self._window.height()), config.SHIFTED)

    def action_select_bod(self):
        self.process_movement(Point(-self._cursor.x, -self._cursor.y), config.SHIFTED)

    def action_select_eod(self):
        if self._doc:
            m = self._doc.size() - self._cursor.y
            n = self._doc.get_row(-1).get_logical_len() - self._cursor.x
            self.process_movement(Point(n, m), config.SHIFTED)

    def action_copy(self):
        if self._selection is not None:
            text = self.get_selection_text()
            pyperclip.copy(text)

    def action_paste(self):
        self.delete_selection()
        text = pyperclip.paste()
        self.insert_text(text)

    def action_undo(self):
        self._doc.undo()

    def action_next_tab(self):
        self.switch_tab(True)

    def action_prev_tab(self):
        self.switch_tab(False)
