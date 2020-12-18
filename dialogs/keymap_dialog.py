from geom import Rect
from config import assign_key, save_keymap, get_assigned_key
from window import Window
from dialogs.dialog import Dialog
from dialogs.wlist import ListWidget
from dialogs.button import Button
from dialogs.text_widget import TextWidget
from dialogs.key_widget import KeyWidget
from utils import center_rect
from focus import action_list


class KeymapDialog(Dialog):
    def __init__(self):
        super().__init__(Window(center_rect(40, 16)))

        self._search_text = TextWidget(self.subwin(3, 1, 18, 3))
        self._search_text.set_title('Search')
        self._search_text.set_editable(True)
        self.add_widget(self._search_text)
        self._search_text.listen('modified', self.on_search)

        self._key_field = KeyWidget(self.subwin(23, 3, 14, 3))
        self._key_field.set_title('Key')

        self._action_list = ListWidget(self.subwin(3, 4, 18, 11))
        self._action_list.set_title('Actions')
        self._action_list.listen('selection_changed', self.selected_action)
        self.fill_action_list()

        self.add_widget(self._action_list)
        self.add_widget(self._key_field)

        self._assign_button = Button(self.subwin(23, 9, 14, 3), 'Assign')
        self.add_widget(self._assign_button)
        self._assign_button.listen('clicked', self.on_assign)

        self._save_button = Button(self.subwin(23, 12, 14, 3), 'Save')
        self.add_widget(self._save_button)
        self._save_button.listen('clicked', save_keymap)

    def on_search(self):
        self.fill_action_list()

    def fill_action_list(self):
        term = self._search_text.text
        self._action_list.clear()
        for item in sorted(list(action_list)):
            if len(term) == 0 or term in item:
                self._action_list.add_item(item)
        self.selected_action()

    def selected_action(self):
        action, _ = self._action_list.get_selection()
        key = get_assigned_key(action)
        self._key_field.set_text_from_key(key)

    def on_assign(self):
        key = self._key_field.text
        action, _ = self._action_list.get_selection()
        if key and action:
            assign_key(key, action)
