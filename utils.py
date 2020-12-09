from geom import Point, Rect


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
