from window import Window
from dialogs.dialog import FormDialog
from dialogs.wlist import ListWidget
from utils import center_rect
import config


class PluginsDialog(FormDialog):
    def __init__(self):
        super().__init__(Window(center_rect(60, 20)), ['Ok', 'Cancel'])
        self._plugins_list = ListWidget(self.subwin(2, 2, 20, 10))
        self._plugins_list.set_title('All Plugins')
        self._plugins_list.listen('enter', self.activate_plugin)
        self.add_widget(self._plugins_list)
        all_plugins = config.get_installed_plugins()
        for p in all_plugins:
            self._plugins_list.add_item(p)

        self._active_list = ListWidget(self.subwin(25, 2, 20, 10))
        self._active_list.set_title('Active Plugins')
        self._active_list.listen('enter', self.deactivate_plugin)
        self.add_widget(self._active_list)
        active_plugins = config.get_value('active_plugins').split('\n')
        for p in active_plugins:
            self._active_list.add_item(p)

    def activate_plugin(self):
        name = self._plugins_list.get_selection()[0]
        if name not in self._active_list.get_items():
            self._active_list.add_item(name)

    def deactivate_plugin(self):
        index = self._active_list.get_selection()[1]
        self._active_list.remove_item(index)

    def get_active_plugins(self):
        return self._active_list.get_items()
