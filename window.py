from geom import Rect, Point
from config import get_app


class Window:
    def __init__(self, size_preference: Point):
        self.rect = Rect(0, 0, 5, 5)
        self.color = 0
        self.size_preference = size_preference
        self.border = True

    def contains(self, p):
        if not isinstance(p, Point):
            p = Point(p)
        return 0 <= p.x < self.width(), 0 <= p.y < self.height()

    def set_rect(self, rect: Rect):
        self.rect = rect

    def clear(self):
        get_app().fill_rect(self.rect, ' ', 0)

    def width(self):
        w = self.rect.width()
        return w - 2 if self.border else w

    def height(self):
        h = self.rect.height()
        return h - 2 if self.border else h

    def requested_size(self):
        return self.size_preference

    def set_cursor(self, *args):
        p = Point(*args)
        if self.border:
            p = p + Point(1, 1)
        get_app().move(self.rect.pos + p)

    def set_color(self, color):
        self.color = color

    def text(self, s):
        get_app().write(s, self.color)

    def render(self):
        if self.border:
            get_app().draw_frame(self.rect, 0)
