class Point:
    def __init__(self, *args):
        if len(args) == 2:
            self.x = args[0]
            self.y = args[1]
        elif len(args) == 1:
            arg = args[0]
            if isinstance(arg, Point):
                self.x = arg.x
                self.y = arg.y
            elif isinstance(arg, tuple):
                self.x = arg[0]
                self.y = arg[1]
            else:
                raise TypeError()
        else:
            raise RuntimeError(f"Invalid point init: {args}")

    def __str__(self):
        return f'{self.x},{self.y}'

    def move(self, *args):
        if len(args) == 1:
            self.x += args[0].x
            self.y += args[0].y
        elif len(args) == 2:
            self.x += args[0]
            self.y += args[1]

    def clamp_x(self, mn, mx):
        if self.x < mn:
            self.x = mn
        if self.x >= mx:
            self.x = mx

    def clamp_y(self, mn, mx):
        if self.y < mn:
            self.y = mn
        if self.y >= mx:
            self.y = mx - 1

    def clone(self):
        return Point(self.x, self.y)

    def reset(self):
        self.x = -1
        self.y = -1

    def __lt__(self, other):
        if not isinstance(other, Point):
            other = Point(other)
        if self.y == other.y:
            return self.x < other.x
        return self.y < other.y

    def __eq__(self, other):
        if not isinstance(other, Point):
            other = Point(other)
        return self.y == other.y and self.x == other.x

    def __ne__(self, other):
        return not (self == other)

    def __gt__(self, other):
        return not self < other and self != other

    def __le__(self, other):
        return not self > other

    def __ge__(self, other):
        return not self < other

    def __iadd__(self, p):
        if not isinstance(p, Point):
            p = Point(p)
        self.x += p.x
        self.y += p.y
        return self

    def __isub__(self, p):
        if not isinstance(p, Point):
            p = Point(p)
        self.x -= p.x
        self.y -= p.y
        return self

    def __add__(self, p):
        if not isinstance(p, Point):
            p = Point(p)
        return Point(self.x + p.x, self.y + p.y)

    def __sub__(self, p):
        if not isinstance(p, Point):
            p = Point(p)
        return Point(self.x - p.x, self.y - p.y)


class Range:
    def __init__(self, start=Point(-1, -1), stop=Point(-1, -1)):
        self.start = Point(start)
        self.stop = Point(stop)

    def get(self):
        return self.start, self.stop

    def get_ordered(self):
        if self.start <= self.stop:
            return self.get()
        return self.stop, self.start

    def empty(self):
        return self.start == self.stop

    def extend(self, p):
        self.stop = Point(p)


class Rect(object):
    def __init__(self, *args):
        if len(args) == 2 and isinstance(args[0], Point) and isinstance(args[1], Point):
            self.pos = Point(args[0])
            self.size = Point(args[1])
        elif len(args) == 4:
            self.pos = Point(args[0], args[1])
            self.size = Point(args[2], args[3])
        elif len(args) == 1 and isinstance(args[0], Rect):
            self.pos = Point(args[0].pos)
            self.size = Point(args[0].size)
        else:
            raise TypeError()

    def clone(self):
        return Rect(self)

    def move(self, delta: Point):
        self.pos += delta

    def width(self):
        return self.size.x

    def height(self):
        return self.size.y

    def right(self):
        return self.pos.x + self.size.x

    def bottom(self):
        return self.pos.y + self.size.y

    def top_left(self):
        return self.pos

    def inflate(self, d):
        if isinstance(d, Point):
            self.pos -= d
            self.size += d+d
        else:
            self.pos -= Point(d, d)
            self.size += Point(2 * d, 2 * d)
        return self

    def is_point_inside(self, p):
        if not isinstance(p, Point):
            p = Point(p)
        p -= self.pos
        return 0 <= p.x < self.size.x and 0 <= p.y < self.size.y
