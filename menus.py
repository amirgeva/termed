from geom import Point, Rect
from config import get_app
from focus import FocusTarget

# from screen import Screen


class MenuItem(object):
    def __init__(self, title, app=None, action=None):
        self.title = title
        self.app = app
        self.action = action
        self.key = ''
        p = title.index('&')
        if 0 <= p < (len(title) - 1):
            self.key = title[p + 1]

    def activate(self):
        if self.app is not None and self.action is not None:
            self.app.on_action(self.action)



class Menu(FocusTarget):
    def __init__(self, title, parent=None):
        super().__init__()
        self.title = title
        self.parent = parent
        self.pos = Point(0, 0)
        self.key = ''
        self.cur = 0
        self.items = []
        self.width = 4

    def add_item(self, *args):  # title, action = None):
        if len(args) == 1 and isinstance(args[0], MenuItem):
            item = args[0]
        elif len(args) == 1 and isinstance(args[0], Menu):
            item = args[0]
        elif len(args) == 1 and isinstance(args[0], str):
            item = MenuItem(args[0])
        elif len(args) == 3:
            item = MenuItem(args[0], args[1], args[2])
        else:
            raise TypeError()
        self.items.append(item)
        self.width = max(self.width, 2 + len(item.title) - item.title.count('&'))

    def on_key(self, key):
        for item in self.items:
            if item.key == key:
                item.activate()
                return True
        return False

    def action_enter(self):
        item = self.items[self.cur]
        if isinstance(item, MenuItem):
            get_app().close_modal()
            item.activate()

    def action_move_left(self):
        if self.parent:
            self.parent.action_move_up()

    def action_move_right(self):
        if self.parent:
            self.parent.action_move_down()

    def action_move_up(self):
        if isinstance(self.items[self.cur], Menu):
            self.items[self.cur].erase()
        self.cur = self.cur - 1
        if self.cur < 0:
            self.cur = len(self.items) - 1
        if isinstance(self.items[self.cur], Menu):
            get_app().set_focus(self.items[self.cur])

    def action_move_down(self):
        if isinstance(self.items[self.cur], Menu):
            self.items[self.cur].erase()
        self.cur = self.cur + 1
        if self.cur >= len(self.items):
            self.cur = 0
        if isinstance(self.items[self.cur], Menu):
            get_app().set_focus(self.items[self.cur])

    def select_next(self):
        self.cur = (self.cur + 1) % len(self.items)

    def select_prev(self):
        self.cur = (self.cur - 1) % len(self.items)

    def activate_current(self):
        self.items[self.cur].activate()

    def erase(self):
        screen = get_app()
        h = len(self.items) + 3
        r = Rect(self.pos.x, self.pos.y, self.width, h)
        y = r.pos.y
        while y <= r.right():
            screen.move((self.pos.x, y))
            screen.write(' ' * r.width(), 0)
            y = y + 1

    def render(self):
        screen = get_app()
        screen.cursor(False)
        pos = self.pos + Point(1, 0)
        h = len(self.items) + 2
        screen.draw_frame(Rect(self.pos.x, self.pos.y, self.width, h), 4)
        index = 0
        for item in self.items:
            color = 4
            pos += (0, 1)
            screen.move(pos)
            n = 0
            if index == self.cur:
                color = 3
            char_color = color
            for c in item.title:
                if c == '&':
                    char_color = 5
                else:
                    screen.write(c, char_color)
                    char_color = color
                    n = n + 1
            s = ' ' * (self.width - 3 - n)
            screen.write(s, color)
            index += 1


def fill_menu(menu, desc):
    for item in desc:
        if len(item) == 2 and isinstance(item[1], list):
            m = Menu(item[0], menu)
            fill_menu(m, item[1])
            menu.add_item(m)
        elif len(item) == 3:
            title, app, action = item
            menu.add_item(title, app, action)
        else:
            raise RuntimeError(f'Invalid menu item: {item}')


def create_menu():
    app = get_app()
    desc = [('&File', [('&New     Ctrl+N', app, 'file_new'),
                       ('&Open    Ctrl+O', app, 'file_open'),
                       ('&Save    Ctrl+S', app, 'file_save'),
                       ('Save &As       ', app, 'file_save_as'),
                       ('&Exit    Ctrl+Q', app, 'file_exit')
                       ]),
            ('&Edit', [('&Copy          Ctrl+C', app, 'copy'),
                       ('C&ut           Ctrl+X', app, 'cut'),
                       ('&Paste         Ctrl+V', app, 'paste'),
                       ('&Find          Ctrl+F', app, 'find_replace'),
                       ('Find &Again        F3', app, 'find_again'),
                       ('&Record Macro  Ctrl+R', app, 'toggle_macro_record'),
                       ('P&lay Macro    Ctrl+P', app, 'play_macro'),
                       ]),
            ('&Options', [('&Colors', app, 'colors'),
                          ('&Editor', app, 'cfg_editor'),
                          ('&Key Mapping', app, 'keymap_dialog')
                          ]),
            ('&Help', [('&About', app, 'help_about'),
                       ]),
            ]
    bar = Menu('')
    fill_menu(bar, desc)
    return bar
