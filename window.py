from geom import Rect, Point
from config import get_app


class Window:
    def __init__(self, *args):
        if len(args) == 1:
            if isinstance(args[0], Point):
                self.size_preference = Point(args[0])
                self.rect = Rect(0, 0, args[0].x, args[0].y)
            elif isinstance(args[0], Rect):
                self.rect = args[0]
                self.size_preference = Point(self.rect.size)
            else:
                self.rect = Rect(0, 0, 5, 5)
                self.size_preference = Point(5, 5)
        else:
            self.rect = Rect(0, 0, 5, 5)
            self.size_preference = Point(5, 5)
        self._color = 0
        self._border = True
        self._title = ''

    def disable_border(self):
        self._border = False

    def set_title(self, title: str):
        self._title = title

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
        return w - 2 if self._border else w

    def height(self):
        h = self.rect.height()
        return h - 2 if self._border else h

    def requested_size(self):
        return self.size_preference

    def set_cursor(self, *args):
        p = Point(*args)
        if self._border:
            p = p + Point(1, 1)
        get_app().move(self.rect.pos + p)

    def set_color(self, color):
        self._color = color

    def text(self, s):
        get_app().write(s, self._color)

    def render(self):
        if self._border:
            get_app().draw_frame(self.rect, 0)
            if len(self._title) > 0:
                self.render_title()

    def render_title(self):
        if self._border:
            app = get_app()
            app.move(self.rect.pos + Point(1, 0))
            app.write(self._title, 0)

    def subwindow(self, rect: Rect):
        rect.move(self.rect.top_left())
        return Window(rect)
