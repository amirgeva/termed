import sys
import curses
import config
from geom import Rect, Point


class Screen:
    def __init__(self):
        # if 'TERM' not in os.environ:
        #     os.environ['TERM']='xterm-256color'
        self.scr = curses.initscr()
        curses.noecho()
        curses.raw()
        self.scr.keypad(True)
        mx = self.scr.getmaxyx()
        self.size = mx[1], mx[0]
        self.rect = Rect(0, 0, self.size[0], self.size[1])
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, config.get_int('fg1', curses.COLOR_YELLOW),
                         config.get_int('bg1', curses.COLOR_BLUE))
        curses.init_pair(2, config.get_int('fg2', curses.COLOR_WHITE),
                         config.get_int('bg2', curses.COLOR_GREEN))
        curses.init_pair(3, config.get_int('fg3', curses.COLOR_BLACK),
                         config.get_int('bg3', curses.COLOR_WHITE))
        curses.init_pair(4, config.get_int('fg4', curses.COLOR_BLACK),
                         config.get_int('bg4', curses.COLOR_CYAN))
        curses.init_pair(5, config.get_int('fg5', curses.COLOR_YELLOW),
                         config.get_int('bg5', curses.COLOR_BLUE))
        curses.init_pair(6, config.get_int('fg6', curses.COLOR_YELLOW),
                         config.get_int('bg6', curses.COLOR_BLUE))
        curses.init_pair(7, config.get_int('fg7', curses.COLOR_WHITE),
                         config.get_int('bg7', curses.COLOR_RED))
        self.box = '\u250f\u2501\u2513\u2503 \u2503\u2517\u2501\u251b'
        self.tees = '\u2533\u2523\u252b\u253b\u254b'
        sys.stdout.write('\033]12;yellow\007')
        self.dbg = None  # open('screen.log', 'w')

    def width(self):
        return self.size[0]

    def height(self):
        return self.size[1]

    def move(self, pos):
        if not isinstance(pos, Point):
            pos = Point(pos)
        if self.rect.is_point_inside(pos):
            self.scr.move(pos.y, pos.x)
            return True
        return False

    @staticmethod
    def cursor(state):
        curses.curs_set(1 if state else 0)

    def write(self, text, color):
        if self.dbg is not None:
            self.dbg.write(f'write("{text}",{color})\n')
            self.dbg.flush()
        attr = 0
        color = curses.color_pair(color | (attr & 0x7FFF))
        try:
            if isinstance(text, str):
                for i in range(0, len(text)):
                    c = text[i]
                    self.scr.addstr(c, color)
            else:
                self.scr.addch(text, color)
        except curses.error:
            pass

    def fill_rect(self, rect, c, clr):
        self.fill(rect.pos.x, rect.pos.y, rect.width(), rect.height(), c, clr)

    def fill(self, x0, y0, w, h, c, clr):
        for y in range(y0, y0 + h):
            self.move((x0, y))
            self.write(c * w, clr)

    def draw_frame(self, rect: Rect, color: int):
        self.move(rect.pos)
        self.write(self.box[0], color)
        for i in range(rect.width() - 2):
            self.write(self.box[1], color)
        self.write(self.box[2], color)
        for y in range(rect.pos.y + 1, rect.bottom() - 1):
            self.move(Point(rect.pos.x, y))
            self.write(self.box[3], color)
            self.move(Point(rect.right() - 1, y))
            self.write(self.box[5], color)
        self.move(Point(rect.pos.x, rect.bottom() - 1))
        self.write(self.box[6], color)
        for i in range(rect.width() - 2):
            self.write(self.box[7], color)
        self.write(self.box[8], color)

    def draw_frame_text(self, pos: Point, text: str, color: int):
        self.move(pos)
        self.write(self.tees[2], color)
        self.write(text, color)
        self.write(self.tees[1], color)

    def refresh(self):
        self.scr.refresh()

    def getkey(self):
        try:
            self.scr.nodelay(False)
            key = self.scr.getkey()
            if len(key) == 1 and ord(key[0]) == 27:
                self.scr.nodelay(True)
                key = "Alt+" + self.scr.getkey()
                self.scr.nodelay(False)
        except curses.error:
            key = 'ESC'
        return key

    def close(self):
        curses.nocbreak()
        self.scr.keypad(0)
        curses.echo()
        curses.endwin()
        self.scr = None
