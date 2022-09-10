import os
import pickle
from typing import List, Tuple
import config
import logger
import utils
from color import Color
from geom import Point
from plugin import WindowPlugin
from menus import Menu, fill_menu
from dialogs.file_dialog import FileDialog
from .treenode import TreeNode, convert_tree
from .cmake_utils import scan_cmake
from dialogs.find_dialog import FindOptions


class FindInFile:
    def __init__(self, output, root: str, search_term: str):
        self._root = root
        self._search_term = search_term
        self._output = output

    def __call__(self, node: TreeNode):
        path = node.get_path(self._root)
        line_number = 0
        for line in open(path).readlines():
            line_number += 1
            if self._search_term in line:
                self._output.add_text(f'{path}:{line_number} {line.strip()}')


class DirTreePlugin(WindowPlugin):
    def __init__(self):
        super().__init__(Point(20, 0))
        self._offset = 0
        self._search_term = ''
        self._search_results = []
        self._result_index = 0
        self._root = os.getcwd()
        self._tree = TreeNode('', True, None)
        self._all_lines: List[Tuple[str, TreeNode]] = []
        self.scan(self._tree, self._root, 0)
        self._root = config.work_dir
        logger.logwrite(f'DirTreePlugin root={self._root}')
        self._cur_y = -1
        self._targets = []
        self.makefile_path = ''
        if self._root:
            logger.logwrite(f'select root {self._root}')
            self.select_root(self._root)
            if self._tree.child_count() > 0:
                self._cur_y = 0
            self.local_config_path = os.path.join(self._root, '.termed.ini')
            if os.path.exists(self.local_config_path):
                self.load_local_config()
        self.create_menu()
        self._redraw()

    def _set_cur_y(self, y: int):
        self._cur_y = y
        self._ensure_visible()

    def _redraw(self):
        self._all_lines = self._render_to_list(self._tree, 0)

    def shutdown(self):
        expanded = [c.get_path(self._root) for c in self._tree.get_all_expanded()]
        config.local_set_value('dirtree_expanded', ','.join(expanded))
        config.local_set_value('dirtree_cur_y', str(self._cur_y))

    def load_local_config(self):
        expanded_paths = config.local_get_value('dirtree_expanded', '')
        expanded_paths = set([p.strip() for p in expanded_paths.split(',')])
        self._tree.expand_set(expanded_paths, self._root)
        self._set_cur_y(config.local_get_int('dirtree_cur_y', self._cur_y))

    def select_root(self, root):
        self._root = root
        build_folder = os.path.join(root, 'build')
        self.makefile_path = os.path.join(build_folder, 'Makefile')
        using_makefile = False
        logger.logwrite(f'makefile path {self.makefile_path}')
        if os.path.exists(self.makefile_path):
            using_makefile = self.select_makefile(build_folder, self.makefile_path)
        if not using_makefile:
            self._tree = TreeNode('', True, None)
            self.scan(self._tree, self._root, 0)

    def select_makefile(self, build_folder: str, makefile_path: str):
        try:
            pkl_path = os.path.join(build_folder, 'tree.pkl')
            if os.path.exists(pkl_path):
                with open(pkl_path, 'rb') as f:
                    self._root, tree, targets = pickle.load(f)
            else:
                self._root, tree, targets = scan_cmake(build_folder, makefile_path)
                with open(pkl_path, 'wb') as f:
                    pickle.dump((self._root, tree, targets), f)
            self._tree = convert_tree(tree)
            self._targets = targets
            return True
        except RuntimeError:
            return False

    def scan(self, tree, path: str, indent: int):
        entry: os.DirEntry
        for entry in os.scandir(path):
            if not entry.name.startswith('.'):
                if entry.is_dir(follow_symlinks=False):
                    node = TreeNode(entry.name, True, tree)
                    tree.add_child(node)
                    # logwrite(f'{spaces}{entry.name}/')
                    self.scan(node, os.path.join(path, entry.name), indent + 2)
                if entry.is_file(follow_symlinks=False):
                    tree.add_child(TreeNode(entry.name, False, tree))
                    # logwrite(f'{spaces}{entry.name}')

    def _render_to_list(self, node: TreeNode, indent: int):
        lines: List[Tuple[str, TreeNode]] = []
        spaces = ' ' * indent
        for child in node:
            text = child.get_name()
            prefix = ' '
            if child.is_dir():
                prefix = '^' if child.is_expanded() else '>'
            lines.append((f'{spaces}{prefix}{text}', child))
            if child.is_dir() and child.is_expanded():
                lines.extend(self._render_to_list(child, indent + 2))
        return lines

    def render(self):
        super().render()
        w, h = self._window.width(), self._window.height()
        end_visible = min(len(self._all_lines), self._offset + h)
        visible_lines = [utils.clamp_str(p[0], w) for p in self._all_lines[self._offset:end_visible]]
        while len(visible_lines) < self._window.height():
            visible_lines.append(utils.clamp_str('', w))
        for y in range(h):
            self._window.set_cursor(0, y)
            color = Color.TEXT
            if (y + self._offset) == self._cur_y:
                color = Color.TEXT_HIGHLIGHT
            elif (y + self._offset) < len(self._all_lines):
                node = self._all_lines[self._offset + y][1]
                if node.get_bare_name() == config.local_get_value('target'):
                    color = Color.FOCUS
            self._window.text(visible_lines[y], color)

    def on_focus(self):
        super().on_focus()
        config.get_app().cursor(False)

    def action_move_left(self):
        if 0 <= self._cur_y < len(self._all_lines):
            node = self._all_lines[self._cur_y][1]
            p = node.get_parent()
            if p and p.is_dir():
                for y in range(len(self._all_lines)):
                    if self._all_lines[y][1] == p:
                        self._set_cur_y(y)
                        p.set_expanded(False)
                        self._redraw()
                        break

    def action_move_down(self):
        if self._cur_y < (len(self._all_lines) - 1):
            self._cur_y += 1
            self._ensure_visible()

    def action_move_pgdn(self):
        h = self._window.height()
        if self._cur_y < (len(self._all_lines) - h - 1):
            self._cur_y += h
        else:
            self._cur_y = len(self._all_lines) - 1
        self._ensure_visible()

    def action_move_pgup(self):
        h = self._window.height()
        if self._cur_y >= h:
            self._cur_y -= h
        else:
            self._cur_y = 0
        self._ensure_visible()

    def action_move_home(self):
        self._cur_y = 0
        self._ensure_visible()

    def action_move_end(self):
        self._cur_y = len(self._all_lines) - 1
        self._ensure_visible()

    def action_move_up(self):
        if self._cur_y > 0:
            self._cur_y -= 1
            self._ensure_visible()

    def _ensure_visible(self):
        dy = self._cur_y - self._offset
        h = self._window.height()
        if dy < 0 or dy >= h:
            self._offset = max(self._cur_y - h // 2, 0)
            self.render()

    def action_enter(self):
        if self._search_term:
            self.perform_search()
            self._search_term = ''
        elif self._cur_y < len(self._all_lines):
            cur_node = self._all_lines[self._cur_y][1]
            if cur_node.is_dir():
                cur_node.toggle_expand()
                self._redraw()
            else:
                config.get_app().open_file(cur_node.get_path(self._root))

    def dfs_iterate(self, node: TreeNode, cb):
        for child in node:
            if child.is_dir():
                self.dfs_iterate(child, cb)
            else:
                cb(child)

    def dfs_search(self, node: TreeNode, term: str):
        results = []
        for child in node:
            if child.is_dir():
                results.extend(self.dfs_search(child, term))
            else:
                if term in child.get_name().lower():
                    results.append(child)
        return results

    def clear_search(self):
        self._search_term = ''

    def process_text_key(self, key: str):
        self._search_term += key

    def perform_search(self):
        self._search_results = self.dfs_search(self._tree, self._search_term.lower())
        self._search_results.sort(key=lambda x: x.get_name())
        self._search_results.sort(key=lambda x: x.get_path(self._root).count('/'))
        self._result_index = 0
        self.show_search_result()

    def show_search_result(self):
        if self._search_results:
            res = self._search_results[self._result_index]
            res.expand_tree()
            self._redraw()
            self.render()
            for y in range(len(self._all_lines)):
                node = self._all_lines[y][1]
                if node is res:
                    self._set_cur_y(y)
                    break

    def global_action_find_in_files(self):
        options = FindOptions()
        output = config.get_app().get_plugin('output')
        output.clear()
        cb = FindInFile(output, self._root, options.find_text)
        self.dfs_iterate(self._tree, cb)

    def action_find_replace_next(self):
        if self._search_results:
            self._result_index = (self._result_index + 1) % len(self._search_results)
            self.show_search_result()

    def action_build_type(self):
        pass

    def process_key(self, key: str):
        if len(key) == 1:
            code = ord(key)
            if 32 <= code < 127:
                self.process_text_key(key)
            else:
                self.clear_search()
        else:
            self.clear_search()

    def on_action(self, action: str):
        super().on_action(action)
        self.clear_search()

    def action_select_root(self):
        d = FileDialog('SelDir')
        config.get_app().set_focus(d)
        config.get_app().event_loop(True)
        r = d.get_result()
        if r == 'Select':
            config.set_value('root', d.directory.text)
            self.select_root(d.directory.text)

    def action_set_target(self):
        if self._cur_y < len(self._all_lines):
            node = self._all_lines[self._cur_y][1]
            sel = node.get_bare_name()
            logger.logwrite(f'Trying to set target to "{sel}"')
            if sel in self._targets:
                config.local_set_value('target', sel)

    def create_menu(self):
        desc = [('&File', [('&Root Dir   Ctrl+O', self, 'select_root'),
                           ('&Set Target', self, 'set_target')
                           ]),
                ('&Options', [('&General', self, 'general_settings'),
                              ('&Build Type', self, 'build_type')
                              ]),
                ]
        bar = Menu('')
        fill_menu(bar, desc)
        self.set_menu(bar)

    def on_click(self, p: Point):
        self._set_cur_y(p.y + self._offset)
        config.get_app().set_focus(self)

    def on_double_click(self, p: Point):
        self._set_cur_y(p.y + self._offset)
        self.action_enter()
