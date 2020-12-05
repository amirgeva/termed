import sys
import os
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
        sys.stdout.write('\033]12;yellow\007')
        self.keylog = None
        self.dbg = open('screen.log', 'w')

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

    def cursor(self, state):
        curses.curs_set(1 if state else 0)

    def write(self, text, color):
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
        self.fill(rect.tl.x, rect.tl.y, rect.width(), rect.height(), c, clr)

    def fill(self, x0, y0, w, h, c, clr):
        for y in range(y0, y0 + h):
            self.move((x0, y))
            self.write(c * w, clr)

    def draw_frame(self, rect, color):
        self.move(rect.tl)
        self.write(curses.ACS_ULCORNER, color)
        for i in range(0, rect.width() - 2):
            self.write(curses.ACS_HLINE, color)
        self.write(curses.ACS_URCORNER, color)
        for y in range(rect.tl.y + 1, rect.br.y):
            self.move(Point(rect.tl.x, y))
            self.write(curses.ACS_VLINE, color)
            self.move(Point(rect.br.x - 1, y))
            self.write(curses.ACS_VLINE, color)
        self.move(Point(rect.tl.x, rect.br.y - 1))
        self.write(curses.ACS_LLCORNER, color)
        for i in range(0, rect.width() - 2):
            self.write(curses.ACS_HLINE, color)
        self.write(curses.ACS_LRCORNER, color)

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
        if False:
            if key == 'KEY_F(24)':  # For debugging purposes
                self.keylog = open('/tmp/key.log', 'w')
            if self.keylog is not None:
                self.keylog.write('{}   {}\n'.format(key, hex(ord(key[0]))))
                self.keylog.flush()
        return key

    def close(self):
        curses.nocbreak()
        self.scr.keypad(0)
        curses.echo()
        curses.endwin()
        self.scr = None
