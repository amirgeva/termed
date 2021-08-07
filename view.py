import typing
import re
from collections import OrderedDict
from cursor import Cursor
from visual_token import VisualToken
from visual_line import VisualLine
from dialogs.find_dialog import FindOptions
import config
from geom import Point, Range
from focus import FocusTarget
from window import Window
from doc import Document
from color import Color, type_colors
from menus import Menu, fill_menu
import pyperclip

word_pattern = re.compile(r'(\w+)')


# noinspection PyTypeChecker
class View(FocusTarget):
    def __init__(self, window: Window, doc: Document = None):
        super().__init__()
        self._window = window
        self._doc = doc
        if doc:
            doc.set_view(self)
            doc.add_modification_callback(self.modification_callback)
        self._visual_offset = Point(0, 0)
        self._selection: Range = None
        self._find_options: FindOptions = None
        self._cursor = Cursor()
        self._last_x = 0
        self._redraw = True
        self._insert = True
        self._current_tab = ''
        self._tabs: typing.OrderedDict[str, dict] = OrderedDict([('', self._generate_tab(Document('', self)))])
        self._menu = Menu('')
        self.create_menu()

    @staticmethod
    def modification_callback(doc: Document, row: int):
        config.get_app().on_modify(doc, row)

    def set_coloring_id(self, coloring_id: str):
        self._doc.set_coloring_id(coloring_id)

    def get_window(self):
        return self._window

    def set_menu(self, menu):
        self._menu = menu

    def get_menu(self):
        return self._menu

    def on_focus(self):
        config.get_app().cursor(True)
        self._window.set_border_type(1)

    def on_leave(self):
        self._window.set_border_type(0)

    def open_tab(self, doc: Document):
        path = doc.get_path()
        if path not in self._tabs:
            self._tabs[path] = self._generate_tab(doc)
        doc.add_modification_callback(self.modification_callback)
        self.switch_tab(path)

    def action_close_tab(self):
        if len(self._tabs) > 0:
            if not config.get_app().save_before_close([self._doc]):
                return
            path = self._doc.get_path()
            keys = list(self._tabs.keys())
            i = keys.index(path)
            next_key = keys[0] if (i + 1) >= len(keys) else keys[i + 1]
            self.switch_tab(next_key)
            del self._tabs[path]
        else:
            config.get_app().action_file_exit()

    def get_all_docs(self):
        res = [self._doc]
        for path in self._tabs:
            res.append(self._tabs.get(path).get('_doc'))
        return res

    def get_all_open_tabs(self):
        res = []
        for path in self._tabs.keys():
            tab = self._tabs.get(path)
            c = tab.get('_cursor')
            res.append(f'{path}:{c.y}:{c.x}')
        c = self.get_cursor()
        res.append(f'{self._current_tab}:{c.y}:{c.x}')
        return ','.join(res)

    def close_empty_tab(self):
        if '' in self._tabs:
            del self._tabs['']

    @staticmethod
    def _generate_tab(doc: Document):
        return {'_doc': doc, '_visual_offset': Point(0, 0), '_selection': None, '_cursor': Cursor()}

    def next_tab(self, delta: int):
        old_path = self._doc.get_path()
        paths = list(self._tabs.keys())
        i = paths.index(old_path)
        n = len(paths)
        i = (i + delta) % n
        new_path = paths[i]
        if old_path != new_path:
            self.switch_tab(new_path)

    def switch_tab(self, new_path):
        old_path = self._doc.get_path()
        if len(self._tabs) == 0 or old_path == new_path:
            return
        tab_fields = ['_doc', '_visual_offset', '_selection', '_cursor']
        new_settings = self._tabs.get(new_path)
        old_settings = {}
        for field in tab_fields:
            old_settings[field] = getattr(self, field)
            setattr(self, field, new_settings.get(field))
        self._tabs[old_path] = old_settings
        self._current_tab = new_path
        config.get_app().on_modify(self._doc, -1)

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
            if self._selection is None or self._selection.empty():
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

    def get_recent_word(self):
        '''
        :return: Current typed word, and an indicator
                 if cursor is not at the beginning of the word
        '''
        c = self._cursor
        line = self._doc.get_row(c.y)
        line_text = line.get_logical_text()
        for token in re.finditer(word_pattern, line_text):
            start = token.start()
            end = token.end()
            if start <= c.x <= end:
                return line_text[start:end], c.x > start
        return '', False

    def complete(self, text: str):
        '''
        Fill in auto complete.   If a partial word is already typed,
        erase it first.
        :param text:
        :return:
        '''
        word, middle = self.get_recent_word()
        if word:
            if middle:
                self.action_move_word_left()
            self.move_cursor(len(word), 0, True)
            self.delete_selection()
        self.insert_text(text)

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

    def get_leading_space(self, y):
        line_text = self._doc.get_row(y).get_logical_text()
        white_prefix = ''
        found = False
        for i in range(len(line_text)):
            if line_text[i] != '\t' and line_text[i] != ' ':
                found = True
                white_prefix = line_text[0:i]
                if line_text[i] == '{':
                    white_prefix += "\t"
                break
        if not found:
            return line_text
        return white_prefix

    def action_enter(self):
        y = self._cursor.y
        white_prefix = self.get_leading_space(y)
        self._doc.split_line(self._cursor)
        self.set_cursor(Cursor(0, self._cursor.y + 1))
        self._doc.insert_text(self.get_cursor(), white_prefix)
        self.set_cursor(Cursor(len(white_prefix), self._cursor.y))
        self.redraw_all()

    def action_delete(self):
        if not self.delete_selection():
            self._doc.delete(self._cursor)

    def action_backspace(self):
        if not self.delete_selection():
            self.set_cursor(self._doc.backspace(self._cursor))

    def process_semantic_highlight(self, y: int, text: str, res: typing.List[VisualToken]):
        semantic_highlights = self._doc.get_semantic_highlights()
        if y in semantic_highlights:
            line = self._doc.get_row(y)
            x = 0
            for col, length, token_type in semantic_highlights.get(y):
                visual_column = line.get_visual_index(col)
                if visual_column > x:
                    res.append(VisualToken(x, text[x:visual_column]))
                    x = visual_column
                res.append(VisualToken(x, text[x:x + length]))
                color = 16
                if token_type in type_colors:
                    color = type_colors.get(token_type)
                res[-1].set_color(color)
                x += length
            if x < len(text):
                res.append(VisualToken(x, text[x:]))
        else:
            res.append(VisualToken(0, text))

    def add_highlights(self, y: int, line: VisualLine) -> typing.List[VisualToken]:
        text = line.get_visual_text()
        res = []
        if self._selection:
            start, stop = self._selection.get_ordered()
            sel_highlight = Color.TEXT_HIGHLIGHT
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
                self.process_semantic_highlight(y, text, res)
        else:
            self.process_semantic_highlight(y, text, res)
        return res

    def draw_cursor_line(self):
        self.draw_line(self._cursor.y - self._visual_offset.y)
        x, y = self.doc2win(self._cursor)
        self._window.set_cursor(x, y)

    def draw_line(self, y: int):
        line_index = y + self._visual_offset.y
        if line_index >= self._doc.size():
            self._window.set_cursor(0, y)
            self._window.text(' ' * self._window.width(), Color.TEXT)
            return
        line = self._doc.get_row(line_index)
        tokens = self.add_highlights(line_index, line)
        x0 = self._visual_offset.x
        x1 = x0 + self._window.width()
        for token in tokens:
            token.clip(x0, x1)
            token.move(-x0)
        cx = 0
        for token in tokens:
            text = token.get_text()
            if len(text) > 0:
                self._window.set_cursor(token.get_pos(), y)
                self._window.text(text, token.get_color())
                cx = cx + len(text)
        if cx < self.width():
            self._window.set_cursor(cx, y)
            color = 0
            if len(tokens) > 0:
                color = tokens[-1].get_color()
            self._window.text(' ' * (self.width() - cx), color)

    def redraw_all(self):
        # self.window.clear()
        for y in range(self.height()):
            self.draw_line(y)
        self._window.set_cursor(self.doc2win(self._cursor))

    def _render_tabs(self):
        if self._window.is_border():
            titles = []
            for path in self._tabs:
                tab = self._tabs.get(path)
                tab_doc = tab.get('_doc')
                tab_title = tab_doc.get_filename() + (' *' if tab_doc.is_modified() else '')
                color = Color.BORDER_HIGHLIGHT if path == self._current_tab else Color.BORDER
                titles.append((tab_title, color))
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
        if not cx:
            self._visual_offset.x = max(0, self._cursor.x - self._window.width() // 2)

    def get_selection_text(self):
        if self._selection is None:
            return ''
        start, stop = self._selection.get_ordered()
        if start.y == stop.y:
            return self._doc.get_row(start.y).get_logical_text()[start.x:stop.x]
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
        self.set_cursor(start)
        self._doc.stop_compound()
        self._selection = None
        return True

    def auto_unindent(self):
        y = self._cursor.y
        if y > 0:
            cur_prefix = self._doc.get_row(y).get_logical_text()
            prev_prefix = self.get_leading_space(y - 1)
            if cur_prefix == prev_prefix and cur_prefix.endswith('\t'):
                self.action_backspace()

    def process_text_key(self, key: str):
        self.delete_selection()
        if key == '}':
            self.auto_unindent()
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
        self.set_cursor(new_cursor)
        self.scroll_display()

    def get_cursor(self) -> Cursor:
        return self._cursor

    def set_cursor(self, cursor: Cursor):
        if isinstance(cursor, Point):
            self._cursor = Cursor(cursor.x, cursor.y)
        elif isinstance(cursor, Cursor):
            self._cursor = cursor
        self.scroll_display()

    def find_replace(self, options: FindOptions):
        self._find_options = options
        self.action_find_replace_next()

    def _find_regex_in_row(self, row_text: str, from_x: int):
        m = self._find_options.regex_pattern.search(row_text, from_x)
        if m:
            return m.start()
        return -1

    def _find_in_row(self, row_text: str, find_text: str, from_x: int):
        if self._find_options.regex:
            return self._find_regex_in_row(row_text, from_x)
        if not self._find_options.case:
            row_text = row_text.upper()
            find_text = find_text.upper()
        try:
            return row_text.index(find_text, from_x)
        except ValueError:
            return -1

    def _find_next(self):
        y = self._cursor.y
        x = self._cursor.x
        find_text = self._find_options.find_text
        while y < self._doc.size():
            row = self._doc.get_row(y)
            text = row.get_logical_text()
            while True:
                x = self._find_in_row(text, find_text, x + 1)
                if x < 0:
                    break
                found = True
                if self._find_options.whole:
                    if x > 0 and text[x - 1].isalnum():
                        found = False
                    if (x + len(find_text)) < len(text) and text[x + len(find_text)].isalnum():
                        found = False
                if found:
                    self.set_cursor(Cursor(x, y))
                    return True
            y = y + 1
            x = 0
        return False

    def action_find_replace_next(self):
        if self._find_options is None or not self._find_options.find_text:
            return
        action = self._find_options.action
        replace = (action == 'Replace')
        replace_all = (action == 'Replace All')
        if replace or replace_all:
            self._doc.start_compound()
        while self._find_next():
            if action == 'Find':
                break
            if replace or replace_all:
                self._doc.replace_text(self._cursor, self._find_options.replace_text, len(self._find_options.find_text))
                if replace:
                    break
        if replace or replace_all:
            self._doc.stop_compound()

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
            m = self._doc.size() - self._cursor.y - 1
            n = self._doc.get_row(-1).get_logical_len() - self._cursor.x
            self.process_movement(Point(n, m), 0)

    def move_word_left(self, flags):
        if self._doc:
            x, y = self._cursor.x, self._cursor.y
            text = self._doc.get_row(y).get_logical_text()
            tokens = list(re.finditer(word_pattern, text[0:x]))
            if tokens:
                self.process_movement(Point(tokens[-1].span()[0] - x, 0), flags)
            elif y > 0:
                if flags == config.SHIFTED:
                    self.action_select_up()
                    self.action_select_end()
                else:
                    self.action_move_up()
                    self.action_move_end()

    def action_move_word_left(self):
        self.move_word_left(0)

    def move_word_right(self, flags):
        if self._doc:
            x, y = self._cursor.x, self._cursor.y
            text = self._doc.get_row(y).get_logical_text()
            text = text[x:]
            tokens = list(re.finditer(word_pattern, text))
            default = True
            if tokens:
                if tokens[0].span()[0] == 0:
                    del tokens[0]
                if tokens:
                    self.process_movement(Point(tokens[0].span()[0], 0), flags)
                    default = False
            if default and y < self._doc.size() - 1:
                if flags == config.SHIFTED:
                    self.action_select_down()
                    self.action_select_home()
                else:
                    self.action_move_down()
                    self.action_move_home()

    def action_move_word_right(self):
        self.move_word_right(0)

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

    def action_select_word_left(self):
        self.move_word_left(config.SHIFTED)

    def action_select_word_right(self):
        self.move_word_right(config.SHIFTED)

    def action_copy(self):
        if self._selection is not None:
            text = self.get_selection_text()
            pyperclip.copy(text)

    def action_cut(self):
        if self._selection is not None:
            text = self.get_selection_text()
            pyperclip.copy(text)
            self.delete_selection()

    def action_paste(self):
        self._doc.start_compound()
        self.delete_selection()
        text = pyperclip.paste()
        self.insert_text(text)
        self._doc.stop_compound()

    def action_undo(self):
        self._doc.undo()

    def action_next_tab(self):
        self.next_tab(1)

    def action_prev_tab(self):
        self.next_tab(-1)

    def create_menu(self):
        app = config.get_app()
        desc = [('&File', [('&New     Ctrl+N', app, 'file_new'),
                           ('&Open    Ctrl+O', app, 'file_open'),
                           ('&Save    Ctrl+S', app, 'file_save'),
                           ('Save &As       ', app, 'file_save_as'),
                           ('&Exit    Ctrl+Q', app, 'file_exit')
                           ]),
                ('&Edit', [('&Copy          Ctrl+C', app, 'copy'),
                           ('C&ut           Ctrl+X', app, 'cut'),
                           ('&Paste         Ctrl+V', app, 'paste'),
                           ('&Find          Ctrl+F', app, 'find_replace'),
                           ('Find &Again        F3', app, 'find_again'),
                           ('&Record Macro  Ctrl+R', app, 'toggle_macro_record'),
                           ('P&lay Macro    Ctrl+P', app, 'play_macro'),
                           ]),
                ('&Options', [('&Colors', app, 'colors'),
                              ('&Editor', app, 'cfg_editor'),
                              ('&Key Mapping', app, 'keymap_dialog'),
                              ('&Plugins', app, 'plugins')
                              ]),
                ('&Help', [('&About', app, 'about'),
                           ]),
                ]
        bar = Menu('')
        fill_menu(bar, desc)
        self.set_menu(bar)
