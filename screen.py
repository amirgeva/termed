import os
import random
import sys
from builtins import staticmethod
import config
from base import Base
from geom import Rect, Point
import _curses

os.environ.setdefault('ESCDELAY', '25')
import curses

color_names = [
]


class Screen(Base):
    def __init__(self):
        super().__init__()
        # if 'TERM' not in os.environ:
        #     os.environ['TERM']='xterm-256color'
        self._scr = curses.initscr()
        curses.flushinp()
        curses.noecho()
        curses.raw()
        self._mouse_callback = None
        self._scr.notimeout(False)
        self._scr.timeout(30)
        self._scr.keypad(True)
        curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)
        mx = self._scr.getmaxyx()
        self._size = mx[1], mx[0]
        self._rect = Rect(0, 0, self._size[0], self._size[1])
        curses.start_color()
        # curses.use_default_colors()
        self._color_names = [
            'Black', 'Navy', 'Blue', 'Grass', 'Turquoise', 'Sky', 'Green', 'Spring', 'Cyan',
            'Brown', 'Purple', 'Violet', 'Gold', 'Gray', 'Slate', 'Green2', 'Green3', 'Cyan2',
            'Red', 'Magenta', 'Pink', 'Orange', 'Salmon', 'Pink2', 'Yellow', 'Sun', 'White'
        ]
        i = 0
        try:
            for r in range(0, 1001, 500):
                for g in range(0, 1001, 500):
                    for b in range(0, 1001, 500):
                        curses.init_color(i, r, g, b)
                        i += 1
            default_pairs = [
                (26, 0), (0, 8), (21, 0), (16, 0), (8, 0), (23, 0), (13, 0)
            ]
            i = 1
            for pair in default_pairs:
                curses.init_pair(i, config.get_int(f'fg{i}', pair[0]), config.get_int(f'bg{i}', pair[1]))
                i = i + 1
            while i < 32:
                curses.init_pair(i, config.get_int(f'fg{i}', random.randint(1, 31)),
                                 config.get_int(f'bg{i}', 0))
                i += 1
        except _curses.error:
            pass
        self._boxes = ['\u250f\u2501\u2513\u2503 \u2503\u2517\u2501\u251b',
                       '\u2554\u2550\u2557\u2551 \u2551\u255a\u2550\u255d']
        self._tees = ['\u2533\u2523\u252b\u253b\u254b', '\u2566\u2560\u2563\u2569\u256c']
        sys.stdout.write('\033]12;yellow\007')
        self.dbg = None  # open('/tmp/screen.log', 'w')

    @staticmethod
    def update_color(color):
        curses.init_pair(color, config.get_int(f'fg{color}', curses.COLOR_YELLOW),
                         config.get_int(f'bg{color}', curses.COLOR_BLUE))

    def get_color_names(self):
        return self._color_names

    @staticmethod
    def query_colors(pair):
        return curses.pair_content(pair)

    def set_mouse_callback(self, cb):
        self._mouse_callback = cb

    def width(self):
        return self._size[0]

    def height(self):
        return self._size[1]

    def move(self, pos):
        if not isinstance(pos, Point):
            pos = Point(pos)
        if self._rect.is_point_inside(pos):
            self._scr.move(pos.y, pos.x)
            return True
        return False

    def cursor_position(self):
        return self._scr.getyx()

    @staticmethod
    def cursor(state):
        curses.curs_set(1 if state else 0)

    def write(self, text, color):
        # if self.dbg is not None:
        #    self.dbg.write(f'write("{text}",{color})\n')
        #    self.dbg.flush()
        attr = 0
        color = curses.color_pair(color | (attr & 0x7FFF))
        # color = 12
        try:
            if isinstance(text, str):
                for i in range(0, len(text)):
                    c = text[i]
                    self._scr.addstr(c, color)
            else:
                self._scr.addch(text, color)
        except curses.error:
            pass

    def fill_rect(self, rect, c, clr):
        self.fill(rect.pos.x, rect.pos.y, rect.width(), rect.height(), c, clr)

    def fill(self, x0, y0, w, h, c, clr):
        for y in range(y0, y0 + h):
            self.move((x0, y))
            self.write(c * w, clr)

    def draw_frame_box(self, rect: Rect, color: int, box):
        self.move(rect.pos)
        self.write(box[0], color)
        for i in range(rect.width() - 2):
            self.write(box[1], color)
        self.write(box[2], color)
        for y in range(rect.pos.y + 1, rect.bottom() - 1):
            self.move(Point(rect.pos.x, y))
            self.write(box[3], color)
            self.move(Point(rect.right() - 1, y))
            self.write(box[5], color)
        self.move(Point(rect.pos.x, rect.bottom() - 1))
        self.write(box[6], color)
        for i in range(rect.width() - 2):
            self.write(box[7], color)
        self.write(box[8], color)

    def draw_frame_text_tees(self, pos: Point, text: str, color: int, tees):
        self.move(pos)
        self.write(tees[2], color)
        self.write(text, color)
        self.write(tees[1], color)

    def draw_frame(self, rect: Rect, color: int, btype: int):
        self.draw_frame_box(rect, color, self._boxes[btype])

    def draw_frame_text(self, pos: Point, text: str, color: int, btype: int):
        self.draw_frame_text_tees(pos, text, color, self._tees[btype])

    def refresh(self):
        self._scr.refresh()

    def flush(self):
        # curses.halfdelay(1)
        try:
            return self._scr.getkey()
        except curses.error:
            return 0

    def getkey(self):
        key = None
        try:
            key = self._scr.getkey()
            if key == "KEY_MOUSE":
                eid, x, y, _, button = curses.getmouse()
                if self._mouse_callback:
                    self._mouse_callback(eid, x, y, button)
            if len(key) == 1 and ord(key[0]) == 27:
                key = 'ESC'
                next_key = self._scr.getkey()
                key = "Alt+" + next_key
        except curses.error as e:
            if e.args[0] == 'no input':
                return key
        except KeyboardInterrupt:
            return chr(3)
        return key

    def close(self):
        curses.nocbreak()
        self._scr.keypad(0)
        curses.echo()
        curses.endwin()
        self._scr = None
