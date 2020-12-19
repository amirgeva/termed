import os
from typing import List
from window import Window
from dialogs.dialog import FormDialog
from dialogs.text_widget import TextWidget
from dialogs.wlist import ListWidget
from utils import center_rect

load_buttons = ['Load', 'Cancel']
save_buttons = ['Save', 'Cancel']


class FileDialog(FormDialog):
    def __init__(self, load: bool):
        super().__init__(Window(center_rect(60, 20)), load_buttons if load else save_buttons)
        self._path = ''
        self._window.set_title('Load' if load else 'Save')
        self._current_directory = os.getcwd()
        self.add_widget(TextWidget(self.subwin(3, 2, 12, 3)).disable_border().set_text('Filename:'))
        self.filename = TextWidget(self.subwin(15, 1, 40, 3))
        self.filename.set_editable(True)
        self.filename.listen('modified', self.filename_modified)
        self.filename.listen('enter', self.filename_enter)
        self.add_widget(self.filename)
        self.set_focus(self.filename)

        self.add_widget(TextWidget(self.subwin(3, 4, 12, 3)).disable_border().set_text('Directory:'))
        self.directory = TextWidget(self.subwin(15, 4, 40, 3))
        self.directory.disable_border()
        self.add_widget(self.directory)

        self.dir_list = ListWidget(self.subwin(3, 5, 23, 11))
        self.dir_list.set_title('Directories')
        self.dir_list.listen('selected', self.selected_directory)
        self.add_widget(self.dir_list)
        self.file_list = ListWidget(self.subwin(27, 5, 30, 11))
        self.file_list.set_title('Files')
        self.file_list.listen('selected', self.selected_file)
        self.add_widget(self.file_list)
        self.set_directory(os.getcwd())

    def selected_directory(self):
        sub_dir = self.dir_list.get_selection()[0]
        self.set_directory(os.path.join(self._current_directory, sub_dir))

    def selected_file(self):
        filename = self.file_list.get_selection()[0]
        self._path = os.path.join(self._current_directory, filename)
        self._buttons[0].action_enter()

    def filename_modified(self):
        if len(self.filename.text) > 0:
            self._path = os.path.join(self._current_directory, self.filename.text)
        else:
            self._path = ''

    def filename_enter(self):
        if self._path:
            self._buttons[0].action_enter()

    def get_path(self):
        return self._path

    def set_directory(self, directory):
        self.dir_list.clear()
        self.file_list.clear()
        self._current_directory = directory
        self.directory.set_text(directory)
        root, dirs, files = next(os.walk(directory))
        for file in files:
            self.file_list.add_item(file)
        self.dir_list.add_item('..')
        for sub_dir in dirs:
            self.dir_list.add_item(sub_dir)
