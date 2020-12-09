#!/usr/bin/env python3
import sys
from geom import Point, Rect
from menus import Menu, create_menu
from doc import Document
from view import View
from screen import Screen
from window import Window
from wm import WindowManager
from utils import call_by_name
import config
import traceback
from dialogs.keymap_dialog import KeymapDialog


class Application(Screen):
    def __init__(self):
        super().__init__()
        self.keylog = open('/tmp/keys', 'w')
        self.menu_bar = Menu('')
        self.shortcuts = {}
        self.views = []
        self.window_manager = WindowManager(Rect(0, 1, self.width(), self.height() - 2))
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
            self.set_focus(view)

    def render(self):
        self.draw_menu_bar()
        self.draw_status_bar()
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
        if hasattr(target, 'on_focus'):
            target.on_focus()

    def close_menu(self):
        self.set_focus(self.views[0])
        self.cursor(True)

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
            if hasattr(self.focus, 'll_key'):
                self.focus.ll_key(key)
            if key in config.keymap:
                action = config.keymap.get(key)
                self.on_action(action)
            else:
                if hasattr(self.focus, 'process_key'):
                    self.focus.process_key(key)
        return True

    def on_action(self, action):
        func_name = f'action_{action}'
        self.keylog.write(f'Action: {action}\n')
        self.keylog.flush()
        if not call_by_name(self,func_name):
            if not call_by_name(self.focus, func_name):
                if hasattr(self.focus, 'on_action'):
                    self.focus.on_action(action)

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

    def draw_status_bar(self):
        self.move((0, self.height() - 1))
        self.write('\u2592' * (self.width() - 1), 0)

    def action_keymap_dialog(self):
        self.set_focus(KeymapDialog())


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
    w = Window(Point(app.width(), app.height()))
    app.window_manager.add_window(w)
    view = View(w, doc)
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
