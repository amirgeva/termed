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


def center_rect(size: Point):
    from config import get_app
    sw = get_app().width()
    sh = get_app().height()
    w, h = size.x, size.y
    return Rect((sw - w) // 2, (sh - h) // 2, w, h)
