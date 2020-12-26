import re
from window import Window
from dialogs.dialog import FormDialog
from dialogs.text_widget import TextWidget
from dialogs.checkbox import CheckboxWidget
from utils import center_rect
from color import Color
import config


class FindOptions:
    def __init__(self):
        self.find_text = config.get_value('last_find', '')
        self.replace_text = config.get_value('last_replace', '')
        self.action = config.get_value('last_find_action', 'Find')
        self.case = config.get_bool('find_case')
        self.whole = config.get_bool('find_whole')
        self.regex = config.get_bool('find_regex')
        self.regex_pattern = None
        self.update_regex()

    def update_regex(self):
        self.regex_pattern = None
        if self.regex and self.find_text:
            flags = 0
            if not self.case:
                flags = re.IGNORECASE
            try:
                self.regex_pattern = re.compile(self.find_text, flags)
            except re.error:
                pass

    def save(self):
        config.set_value('last_find', self.find_text)
        config.set_value('last_replace', self.replace_text)
        config.set_value('last_find_action', self.action)
        config.set_value('find_case', self.case)
        config.set_value('find_whole', self.whole)
        config.set_value('find_regex', self.regex)


class FindDialog(FormDialog):
    def __init__(self):
        super().__init__(Window(center_rect(60, 20)), ['Find', 'Replace', 'Replace All', 'Cancel'])
        self.options = FindOptions()

        self._find_text = TextWidget(self.subwin(2, 2, 40, 3))
        self._find_text.set_title('Find')
        self._find_text.set_editable(True)
        self._find_text.set_text(self.options.find_text, True)
        self._find_text.listen('enter', self.on_find)
        self._find_text.listen('modified', self.update_options)
        self._replace_text = TextWidget(self.subwin(2, 5, 40, 3))
        self._replace_text.set_title('Replace')
        self._replace_text.set_editable(True)
        self._replace_text.set_text(self.options.replace_text, True)
        self._replace_text.listen('enter', self.on_replace)
        self._replace_text.listen('modified', self.update_options)

        self._case = CheckboxWidget(self.subwin(2, 9, 3, 1), self.options.case)
        self._whole = CheckboxWidget(self.subwin(2, 10, 3, 1), self.options.whole)
        self._regex = CheckboxWidget(self.subwin(2, 11, 3, 1), self.options.regex)
        self._case.listen('toggled', self.update_options)
        self._whole.listen('toggled', self.update_options)
        self._regex.listen('toggled', self.update_options)

        self.add_widget(TextWidget(self.subwin(6, 9, 20, 1), 'Case Sensitive'))
        self.add_widget(TextWidget(self.subwin(6, 10, 20, 1), 'Whole Word'))
        self.add_widget(TextWidget(self.subwin(6, 11, 20, 1), 'Regular Expressions'))

        self.add_widget(self._find_text)
        self.add_widget(self._replace_text)
        self.add_widget(self._case)
        self.add_widget(self._whole)
        self.add_widget(self._regex)
        self.set_focus(self._find_text)

    def close(self, result=None):
        if result:
            self.options.action = result
            if result != 'Close':
                self.options.save()
        super().close(result)

    def on_find(self):
        self.close('Find')

    def on_replace(self):
        self.close('Replace')

    def update_options(self):
        self.options.find_text = self._find_text.text
        self.options.replace_text = self._replace_text.text
        self.options.case = self._case.get_state()
        self.options.whole = self._whole.get_state()
        self.options.regex = self._regex.get_state()
        self.options.update_regex()
