from window import Window
from dialogs.dialog import FormDialog
from dialogs.text_widget import TextWidget
from dialogs.checkbox import CheckboxWidget
from utils import center_rect
from color import Color
import config


class FindDialog(FormDialog):
    def __init__(self):
        super().__init__(Window(center_rect(60, 20)), ['Find', 'Replace', 'Replace All', 'Cancel'])
        self._find_text = TextWidget(self.subwin(2, 2, 40, 3))
        self._find_text.set_title('Find')
        self._find_text.set_editable(True)
        self._find_text.set_text(config.get_value('last_find', ''), True)
        self._find_text.listen('enter', self.on_find)
        self._replace_text = TextWidget(self.subwin(2, 5, 40, 3))
        self._replace_text.set_title('Replace')
        self._replace_text.set_editable(True)
        self._replace_text.set_text(config.get_value('last_replace', ''), True)
        self._replace_text.listen('enter', self.on_replace)

        self._case = CheckboxWidget(self.subwin(2, 9, 3, 1))
        self._whole = CheckboxWidget(self.subwin(2, 10, 3, 1))
        self._regex = CheckboxWidget(self.subwin(2, 11, 3, 1))

        self.add_widget(TextWidget(self.subwin(6, 9, 20, 1), 'Case Sensitive'))
        self.add_widget(TextWidget(self.subwin(6, 10, 20, 1), 'Whole Word'))
        self.add_widget(TextWidget(self.subwin(6, 11, 20, 1), 'Regular Expressions'))

        self.add_widget(self._find_text)
        self.add_widget(self._replace_text)
        self.add_widget(self._case)
        self.add_widget(self._whole)
        self.add_widget(self._regex)
        self.set_focus(self._find_text)

    def on_find(self):
        self.close('Find')

    def on_replace(self):
        self.close('Replace')