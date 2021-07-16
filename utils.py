import logger
from dataclasses import dataclass
from geom import Point, Rect
from io import StringIO


class ExitException(Exception):
    pass


def count_leading_spaces(s):
    n = 0
    for c in s:
        if c != ' ':
            break
        n += 1
    return n


def align(s, n):
    if len(s) > n:
        return s[0:n]
    if len(s) < n:
        return s + ' ' * (n - len(s))
    return s


def ctrl(key):
    return chr(ord(key) - ord('A') + 1)


def center_rect(*args):
    size = Point(*args)
    from config import get_app
    sw = get_app().width()
    sh = get_app().height()
    w, h = size.x, size.y
    return Rect((sw - w) // 2, (sh - h) // 2, w, h)


def fit_text(text, width):
    if len(text) > width:
        return text[0:width]
    if len(text) < width:
        return text + ' ' * (width - len(text))
    return text


def center_text(text, width):
    if len(text) > width:
        return text[0:width]
    if len(text) < width:
        wl = width - len(text)
        w1 = wl // 2
        w2 = wl - w1
        return ' ' * w1 + text + ' ' * w2
    return text


def call_by_name(obj, func_name, *args):
    if hasattr(obj, func_name):
        f = getattr(obj, func_name)
        f(*args)
        return True
    return False


def clamp_str(s, n, add_spaces: bool = True):
    if len(s) > n:
        return s[0:n]
    if len(s) < n:
        return s + ' ' * (n - len(s))
    return s


class TabExpander:
    def __init__(self, tab_size: int = 4):
        self._tab_size: int = tab_size
        self._tab_indices = []

    def expand(self, text: str):
        sio = StringIO()
        vi = 0
        for c in text:
            if c == '\t':
                space_count = self._tab_size - (vi % self._tab_size)
                sio.write(' ' * space_count)
                vi += space_count
            else:
                sio.write(c)
                vi += 1
        return sio.getvalue()


@dataclass
class ColoringItem:
    row: int
    col: int
    length: int
    type_name: str


def parse_coloring_data(data, tokens):
    res = []
    # logger.logwrite(str(data))
    n = len(data)
    i = 0
    prev_row = 0
    prev_col = 0
    while i < n:
        row = data[i] + prev_row
        if row != prev_row:
            prev_col = 0
        col = data[i + 1] + prev_col
        prev_row = row
        prev_col = col
        length = data[i + 2]
        type_index = data[i + 3]
        # mod_bits = data[i + 4]
        i += 5
        try:
            type_name = tokens[type_index]
        except IndexError:
            type_name = "Unknown"
        res.append(ColoringItem(row, col, length, type_name))
    return res


def parse_coloring_message(msg, tokens):
    res = []
    if 'result' not in msg:
        return res, ''
    result = msg['result']
    result_id = result['resultId']
    data = []
    if 'data' in result:
        res.extend(parse_coloring_data(result['data'], tokens))
    if 'edits' in result:
        edits = result['edits']
        for edit in edits:
            data = edit['data']
            del_count = edit['deleteCount']
            start = edit['start']
            res.extend(parse_coloring_data(data, tokens))
    return res, result_id
