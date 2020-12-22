#!/usr/bin/env python3
import sys
import os
from typing import List

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
from focus import FocusTarget
from dialogs.keymap_dialog import KeymapDialog
from dialogs.prompt_dialog import PromptDialog
from dialogs.file_dialog import FileDialog


class Application(Screen):
    def __init__(self):
        super().__init__()
        self.menu_bar = Menu('')
        self.shortcuts = {}
        self.views = []
        self._modal = False
        self.window_manager = WindowManager(Rect(0, 1, self.width(), self.height() - 2))
        self.focus = None
        self.terminating = False
        FocusTarget.add(self)

    def event_loop(self, modal):
        self._modal = modal
        if modal:
            self.render()
        while self.process_input() and self._modal == modal:
            self.render()
            self.place_cursor()

    def message_box(self, text):
        self.focus = PromptDialog('Message', text, ['Ok'])
        self.event_loop(True)

    def save_before_close(self, docs: List[Document]):
        for doc in docs:
            if doc.is_modified():
                d = PromptDialog('Exit', 'Save file?', ['Yes', 'No', 'Cancel'])
                self.focus = d
                self.event_loop(True)
                r = d.get_result()
                if r == 'Yes':
                    if not self.action_file_save():
                        return False
                elif r == 'No':
                    pass
                else:
                    return False
        return True

    def action_file_exit(self):
        if isinstance(self.focus, View):
            if not self.save_before_close(self.focus.get_all_docs()):
                return False
        self.terminating = True
        return True

    def action_file_save(self):
        if isinstance(self.focus, View):
            doc = self.focus.get_doc()
            filename = doc.get_filename()
            if not filename:
                return self.action_file_save_as()
            else:
                doc.save()
                self.render()
            return True

    def action_file_save_as(self):
        if isinstance(self.focus, View):
            focus: View = self.focus
            d = FileDialog(False)
            self.focus = d
            self.event_loop(True)
            r = d.get_result()
            if r == 'Save':
                focus.get_doc().save(d.get_path())
                self.render()
                return True
        return False

    def action_file_open(self):
        if isinstance(self.focus, View):
            focus: View = self.focus
            d = FileDialog(True)
            self.focus = d
            self.event_loop(True)
            r = d.get_result()
            if r == 'Load':
                focus.open_tab(Document(d.get_path()))
                self.render()
                return True
        return False

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

    def close_modal(self):
        self.set_focus(self.views[0])
        self._modal = False
        self.cursor(True)

    def modal_result(self, result):
        pass

    def process_input(self):
        if self.terminating:
            return False
        key = self.getkey()
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
        if not call_by_name(self, func_name):
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
    config.get_app().message_box(text)


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
    # noinspection PyBroadException
    try:
        app.event_loop(False)
    except Exception:
        error_report = traceback.format_exc()
    app.close()
    print(error_report)


if __name__ == '__main__':
    main()
