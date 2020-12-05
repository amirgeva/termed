#!/usr/bin/env python3
import sys
from geom import Point, Rect
from menus import Menu, create_menu
from doc import Document
from view import View
from screen import Screen
from window import Window
from utils import ExitException
import config
import traceback


class Application(Screen):
    def __init__(self):
        super().__init__()
        self.keylog = open('/tmp/keys', 'w')
        self.menu_bar = Menu('')
        self.shortcuts = {}
        self.views = []
        self.focus = None
        self.terminating = False

    def on_file_exit(self):
        self.terminating = True

    def set_menu(self, bar):
        self.menu_bar = bar
        if len(bar.items) > 0:
            self.shortcuts['KEY_F(10)'] = bar.items[0]

    def add_view(self, view):
        self.views.append(view)
        if self.focus is None:
            self.focus = view

    def render(self):
        self.draw_menu_bar()
        for view in self.views:
            if view is not self.focus:
                view.render()
        if self.focus is not None:
            self.focus.render()

    def process_shortcuts(self, key):
        if key in self.shortcuts:
            self.set_focus(self.shortcuts.get(key))
            return True
        return False

    def set_focus(self, target):
        self.focus = target

    def process_input(self):
        if self.terminating:
            return False
        key = self.getkey()
        if self.keylog:
            self.keylog.write(f'{type(key)}: n={len(key)}  "{key}"  {ord(key[-1])}\n')
            self.keylog.flush()
        if key == 'KEY_F(12)':
            return False
        if self.process_shortcuts(key):
            return True
        if self.focus is not None:
            if key in config.keymap:
                action, flags = config.keymap.get(key)
                if hasattr(self.focus, action):
                    func = getattr(self.focus, action)
                    func(flags)
            else:
                if hasattr(self.focus, 'process_key'):
                    self.focus.process_key(key)
        return True

    def place_cursor(self):
        if self.focus is not None and hasattr(self.focus, 'place_cursor'):
            self.focus.place_cursor()

    def draw_menu_bar(self):
        color = 4
        self.move((0, 0))
        self.write(' ' * self.width(), color)
        self.move((1, 0))
        pos = Point(2, 1)
        for item in self.menu_bar.items:
            title = item.title
            item.pos = Point(pos)
            pos += Point(len(title) - title.count('&') + 3, 0)
            self.write('[', color)
            rev = False
            char_color = color
            for c in title:
                if c == '&':
                    char_color = color + 1
                    rev = True
                else:
                    if rev:
                        rev = False
                        self.shortcuts['Alt+' + c.upper()] = item
                        self.shortcuts['Alt+' + c.lower()] = item
                    self.write(c, char_color)
                    char_color = color
            self.write('] ', color)


def message_box(text):
    pass


def main():
    app = Application()
    config.app = app
    filename = ''
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    doc = Document(filename)
    doc.load(filename)
    view = View(Window(app, Rect(3, 3, app.width() - 5, app.height() - 5)), doc)
    app.set_menu(create_menu())
    app.add_view(view)
    app.render()
    view.redraw_all()
    error_report = ''
    try:
        while app.process_input():
            app.render()
            app.place_cursor()
    except Exception:
        error_report = traceback.format_exc()
    app.close()
    print(error_report)


if __name__ == '__main__':
    main()
