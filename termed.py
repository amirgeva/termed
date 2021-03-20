#!/usr/bin/env python3
import sys
from typing import List, Dict
from geom import Rect
from menus import Menu, create_menu
from doc import Document
from view import View
from screen import Screen
from wm import WindowManager
from utils import call_by_name
from plugin import *
import config
import traceback
from focus import FocusTarget
from dialogs.dialog import Dialog
from dialogs.keymap_dialog import KeymapDialog
from dialogs.prompt_dialog import PromptDialog
from dialogs.file_dialog import FileDialog
from dialogs.color_dialog import ColorDialog
from dialogs.find_dialog import FindDialog
from dialogs.plugins_dialog import PluginsDialog


class Application(Screen):
    def __init__(self):
        super().__init__()
        self.menu_bar = Menu('')
        self.shortcuts = {}
        self.main_view=None
        self.views = []
        self._modal = False
        self.window_manager = WindowManager(Rect(0, 1, self.width(), self.height() - 2))
        self.focus = None
        self.terminating = False
        self.active_plugins: Dict[str, Plugin] = {}
        FocusTarget.add(self)
        # self.activate_plugins()

    def set_main_view(self, view):
        self.main_view=view
        self.add_view(view)

    def event_loop(self, modal):
        self._modal = modal
        if modal:
            self.render()
        while self.process_input() and self._modal == modal:
            self.render()
            self.place_cursor()

    def modal_dialog(self, d: Dialog):
        self.focus = d
        self.event_loop(True)

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

    #    def action_plugin_test(self):
    #        pl = WindowPlugin()
    #        self.active_plugins.append(pl)
    #        self.window_manager.add_window(pl.get_window())

    def action_file_exit(self):
        if isinstance(self.focus, View):
            if not self.save_before_close(self.focus.get_all_docs()):
                return False
        self.terminating = True
        return True

    def action_file_save(self):
        if isinstance(self.main_view, View):
            doc = self.main_view.get_doc()
            filename = doc.get_filename()
            if not filename:
                return self.action_file_save_as()
            else:
                doc.save()
                self.render()
            return True

    def action_file_save_as(self):
        if isinstance(self.main_view, View):
            d = FileDialog(False)
            self.focus = d
            self.event_loop(True)
            r = d.get_result()
            if r == 'Save':
                self.main_view.get_doc().save(d.get_path())
                self.render()
                return True
        return False

    def action_file_new(self):
        if isinstance(self.main_view, View):
            self.main_view.open_tab(Document(''))
            self.render()

    def open_file(self, path):
        self.main_view.open_tab(Document(path))
        self.set_focus(self.main_view)
        self.render()

    def action_file_open(self):
        if isinstance(self.focus, View):
            d = FileDialog(True)
            self.focus = d
            self.event_loop(True)
            r = d.get_result()
            if r == 'Load':
                self.main_view.open_tab(Document(d.get_path()))
                self.render()
                return True
        return False

    def action_find_replace(self):
        d = FindDialog()
        self.focus = d
        self.event_loop(True)
        r = d.get_result()
        if r and r != 'Close':
            if isinstance(self.focus, View):
                self.focus.find_replace(d.options)

    def action_plugins(self):
        if not config.plugins_exist():
            d = PromptDialog('Plugins', 'Clone Plugins?', ['Yes', 'No'])
            self.focus = d
            self.event_loop(True)
            if d.get_result() == 'Yes':
                if not config.clone_plugins():
                    self.focus = PromptDialog('Error', 'Failed to clone plugins', ['Ok'])
                    self.event_loop(True)
                    return
            else:
                return
        d = PluginsDialog()
        self.focus = d
        self.event_loop(True)
        if d.get_result() == 'Ok':
            config.set_value('active_plugins', '\n'.join(d.get_active_plugins()))
            self.activate_plugins()

    def activate_plugins(self):
        cfg_plugins = set(config.get_value('active_plugins').split('\n'))
        current = self.active_plugins.keys()
        new_active = {}
        for name in current:
            p = self.active_plugins.get(name)
            if name not in cfg_plugins:
                p.deactivate()
            else:
                new_active[name] = p
        for name in cfg_plugins:
            if name not in new_active:
                p = config.create_plugin(name)
                new_active[name] = p
                p.activate()
                if isinstance(p, WindowPlugin):
                    self.window_manager.add_window(p.get_window())
                    self.add_view(p)
        self.active_plugins = new_active

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
        # for plugin_name in self.active_plugins:
        #    plugin = self.active_plugins.get(plugin_name)
        #    if plugin is not self.focus:
        #        plugin.render()
        if self.focus is not None:
            self.focus.render()

    def process_shortcuts(self, key):
        if key in self.shortcuts:
            self.set_focus(self.shortcuts.get(key))
            return True
        return False

    def set_focus(self, target):
        if self.focus != target:
            if self.focus is not None and hasattr(self.focus, 'on_leave'):
                self.focus.on_leave()
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

    def action_colors(self):
        self.set_focus(ColorDialog())

    def action_next_view(self):
        n = len(self.views)
        if n <= 1:
            return
        for view, i in zip(self.views, range(n)):
            if view == self.focus:
                self.set_focus(self.views[(i + 1) % n])
                return


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
    app.set_main_view(view)
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
