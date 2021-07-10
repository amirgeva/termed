import os
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
        if self._root:
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
        makefile_path = os.path.join(root, 'Makefile')
        using_makefile = False
        if os.path.exists(makefile_path):
            using_makefile = self.select_makefile(root, makefile_path)
        if not using_makefile:
            self._tree = TreeNode('', True, None)
            self.scan(self._tree, self._root, 0)

    def select_makefile(self, build_folder: str, path: str):
        self._root, tree = scan_cmake(build_folder, path)
        self._tree = convert_tree(tree)
        return True

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
            color = Color.TEXT_HIGHLIGHT if (y + self._offset) == self._cur_y else Color.TEXT
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

    def dfs_search(self, node: TreeNode, term: str):
        results = []
        for child in node:
            if child.is_dir():
                results.extend(self.dfs_search(child, term))
            else:
                if term in child.get_name():
                    results.append(child)
        return results

    def clear_search(self):
        self._search_term = ''

    def process_text_key(self, key: str):
        self._search_term += key

    def perform_search(self):
        self._search_results = self.dfs_search(self._tree, self._search_term)
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

    def action_find_replace_next(self):
        if self._search_results:
            self._result_index = (self._result_index + 1) % len(self._search_results)
            self.show_search_result()

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

    def create_menu(self):
        desc = [('&File', [('&Root Dir   Ctrl+O', self, 'select_root')
                           ]),
                ('&Options', [('&General', self, 'general_settings')
                              ]),
                ]
        bar = Menu('')
        fill_menu(bar, desc)
        self.set_menu(bar)
