from screen import Screen
from geom import Rect, Point


class Window:
    def __init__(self, screen: Screen, rect: Rect):
        self.screen = screen
        self.rect = rect
        self.color = 0

    def clear(self):
        self.screen.fill_rect(self.rect, ' ', 0)

    def width(self):
        return self.rect.width()

    def height(self):
        return self.rect.height()

    def set_cursor(self, *args):
        p = Point(*args)
        self.screen.move(self.rect.tl + p)

    def set_color(self, color):
        self.color = color

    def text(self, s):
        self.screen.write(s, self.color)
