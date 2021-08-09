#!/usr/bin/env python3
import sys
import os
from typing import List, Dict
from collections import defaultdict
import json

from cursor import Cursor
from doc import Document
from view import View
from screen import Screen
from wm import WindowManager
from utils import *
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
from dialogs.wlist import ListWidget
from lspclient.client import LSPClient


class Application(Screen):
    # noinspection PyTypeChecker
    def __init__(self):
        super().__init__()
        self.menu_bar = Menu('')
        self.shortcuts = {}
        self.main_view: View = None
        self.output_view: View = None
        self.views = []
        self._modal = False
        self.window_manager = WindowManager(Rect(0, 1, self.width(), self.height() - 2))
        self.focus = None
        self.terminating = False
        self.modified = True
        self.active_plugins: Dict[str, Plugin] = {}
        self._root = config.work_dir
        self.lsp = LSPClient(self._root)
        FocusTarget.add(self)
        # noinspection PyTypeChecker
        self._completion_list: ListWidget = None
        self._completion_items: Dict[str, List[str]] = defaultdict(list)

    def close(self):
        open_docs = self.main_view.get_all_open_tabs()
        config.local_set_value('open_docs', open_docs)
        super().close()
        self.lsp.shutdown()
        for plugin_name in self.active_plugins:
            self.active_plugins[plugin_name].shutdown()

    def get_plugin(self, name):
        if name in self.active_plugins:
            return self.active_plugins.get(name)
        return None

    def reopen_session(self):
        paths = [path for path in config.local_get_value('open_docs').split(',') if path]
        logger.logwrite(paths)
        open_count = 0
        for path in paths:
            parts = path.split(':')
            cur = parts[0]
            row = 0
            col = 0
            if len(parts) > 2:
                row = int(parts[1])
                col = int(parts[2])
            if cur:
                logger.logwrite(f'Opening "{cur}" at row={row}, col={col}')
                self.open_file(cur, row, col)
                open_count += 1
        if open_count > 0:
            self.main_view.close_empty_tab()

    def handle_full_coloring(self, msg):
        self.main_view.get_doc().clear_semantic_highlight(-1)
        self.handle_coloring(msg)

    def handle_row_coloring(self, msg):
        self.handle_coloring(msg)

    def handle_coloring(self, msg):
        if 'error' in msg:
            logger.logwrite(msg['error'])
            return
        tokens, _ = self.lsp.get_coloring_legend()
        coloring, result_id = parse_coloring_message(msg, tokens)
        self.main_view.set_coloring_id(result_id)
        for item in coloring:
            self.main_view.get_doc().clear_semantic_highlight(item.row)
        for item in coloring:
            self.main_view.get_doc().add_semantic_highlight(item.row, item.col, item.length, item.type_name)

    def set_main_view(self, view):
        self.main_view = view
        self.add_view(view)
        self.set_menu(view.get_menu())

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
        paths = []
        for doc in docs:
            if doc.is_modified():
                d = PromptDialog('Exit', 'Save file?', ['Yes', 'No', 'Cancel'])
                self.focus = d
                self.event_loop(True)
                r = d.get_result()
                if r == 'Yes':
                    # TODO: Change to save current iter doc
                    if not self.action_file_save():
                        return False
                elif r == 'No':
                    pass
                else:
                    return False
            paths.append(doc.get_path())
        for path in paths:
            self.lsp.close_source_file(path)
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
            d = FileDialog('Save')
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
            self.main_view.open_tab(Document('', self.main_view))
            self.render()

    def open_file(self, path, row=-1, col=-1):
        try:
            self.main_view.open_tab(Document(path, self.main_view))
            self.lsp.open_source_file(path)
            self.set_focus(self.main_view)
            if row >= 0 and col >= 0:
                row = min(row, self.main_view.get_doc().size() - 1)
                self.main_view.set_cursor(Cursor(col, row))
            self.render()
        except IOError:
            d = PromptDialog('Error', f'File {path} not found', ['Ok'])
            self.focus = d
            self.event_loop(True)

    def action_file_open(self):
        if isinstance(self.focus, View):
            d = FileDialog('Load')
            self.focus = d
            self.event_loop(True)
            r = d.get_result()
            if r == 'Load':
                self.open_file(d.get_path())
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
        d = PluginsDialog()
        self.focus = d
        self.event_loop(True)
        if d.get_result() == 'Ok':
            config.set_value('active_plugins', ' '.join(d.get_active_plugins()))
            self.activate_plugins()

    def activate_plugins(self):
        cfg_plugins = set(config.get_value('active_plugins', 'output').split(' '))
        current = self.active_plugins.keys()
        new_active: Dict[str, Plugin] = {}
        for name in current:
            p = self.active_plugins.get(name)
            if name not in cfg_plugins:
                p.deactivate()
            else:
                new_active[name] = p
        for name in cfg_plugins:
            if name not in new_active:
                p = config.create_plugin(name)
                if p:
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
        if self._completion_list is not None:
            self._completion_list.render()

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
            if hasattr(target, 'get_menu'):
                self.set_menu(target.get_menu())

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
        if key is None:
            self.on_no_input()
            return True
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
                    if key == '.' and hasattr(self.focus, 'get_doc'):
                        self.get_suggestions()
                    # logger.logwrite(f'key: {key}')
        return True

    def on_no_input(self):
        if self.modified:
            doc = self.main_view.get_doc()
            path = doc.get_path()
            if os.path.isfile(path):
                self.lsp.request_coloring(path, '', self.handle_full_coloring)
            self.modified = False

    def on_modify(self, doc: Document, row: int):
        path = doc.get_path()
        self.modified = True
        if self._completion_list:
            self.update_completion_list()
        if self.lsp.is_open_file(path):
            if row < 0:
                self.lsp.modify_source_file(path, self.focus.get_doc().get_text(True))
                # self.lsp.request_coloring(path, '', self.handle_full_coloring)
            else:
                self.lsp.modify_source_line(path, row, doc.get_row(row).get_logical_text())
                # self.lsp.request_coloring(path, doc.get_last_coloring_id(), self.handle_row_coloring)

    def update_completion_list(self):
        word, _ = self.main_view.get_recent_word()
        self._completion_list.clear()
        for name in sorted(self._completion_items.keys()):
            if word:
                if word in name:
                    self._completion_list.add_item(name)
            else:
                self._completion_list.add_item(name)

    def get_suggestions(self):
        doc: Document = self.focus.get_doc()
        path = doc.get_path()
        if self.lsp.is_open_file(path):
            self.lsp.modify_source_file(path, doc.get_text(True))
            cursor = self.focus.get_cursor()
            col, row = cursor.x, cursor.y
            self.lsp.request_completion(path, row, col, self.handle_suggestions)

    def tip_rect(self):
        w, h = self.size
        wr = Rect(0, 0, w, h)
        tw, th = 40, 20
        y, x = self.cursor_position()
        r1 = Rect(x, y + 1, tw, th)
        r2 = Rect(x, y - th, tw, th)
        r1 = wr.intersection(r1)
        r2 = wr.intersection(r2)
        return r1 if r1.area() > r2.area() else r2

    def handle_suggestions(self, msg):
        logger.logwrite(json.dumps(msg, indent=4, sort_keys=True))
        if 'result' in msg and 'items' in msg['result']:
            # self._completion_list = ListWidget(Window(Rect(x, y + 1, 30, 5)))
            self._completion_list = ListWidget(Window(self.tip_rect()))
            self._completion_list.listen('enter', self._use_suggestion)
            items = msg['result']['items']
            self._completion_items = defaultdict(list)
            for item in items:
                self._completion_items[item['filterText']].append(item['label'])
            for name in sorted(self._completion_items.keys()):
                self._completion_list.add_item(name)

    def _use_suggestion(self):
        if self._completion_list is None:
            return
        selection, _ = self._completion_list.get_selection()
        logger.logwrite(f'Selected: "{selection}"')
        self._completion_list = None
        self.main_view.complete(selection)

    def on_action(self, action):
        if not super().on_action(action):
            func_name = f'action_{action}'
            if self._completion_list is not None:
                if call_by_name(self._completion_list, func_name):
                    return False
            if call_by_name(self.focus, func_name):
                return False
            for plugin_name in self.active_plugins.keys():
                plugin = self.active_plugins.get(plugin_name)
                if call_by_name(plugin, 'global_' + func_name):
                    return True
            if hasattr(self.focus, 'on_action'):
                self.focus.on_action(action)
        return False

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

    def action_suggestions(self):
        self.get_suggestions()

    def action_keymap_dialog(self):
        self.set_focus(KeymapDialog())

    def action_colors(self):
        self.set_focus(ColorDialog())

    def action_escape(self):
        if self._completion_list:
            self._completion_list = None
            self._completion_items = defaultdict(list)
        return False

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
    input()
    app = Application()
    config.app = app
    filename = ''
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    doc = Document(filename, None)
    doc.load(filename)
    w = Window(Point(app.width(), app.height()))
    app.window_manager.add_window(w)
    view = View(w, doc)
    app.set_main_view(view)
    app.reopen_session()
    app.render()
    view.redraw_all()
    error_report = ''
    app.activate_plugins()
    app.render()
    view.redraw_all()
    # noinspection PyBroadException
    try:
        app.event_loop(False)
    except Exception:
        error_report = traceback.format_exc()
    app.close()
    print(error_report)


if __name__ == '__main__':
    main()
