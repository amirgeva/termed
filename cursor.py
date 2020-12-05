from geom import Point


class Cursor(Point):
    def __init__(self, x=0, y=0):
        super().__init__(x, y)

    def clone(self):
        return Cursor(self.x, self.y)
