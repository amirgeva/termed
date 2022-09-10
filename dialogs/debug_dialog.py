from window import Window
from dialogs.dialog import FormDialog
from dialogs.text_widget import TextWidget
from dialogs.checkbox import CheckboxWidget
from utils import center_rect
import config


class DebugDialog(FormDialog):
    def __init__(self, target: str):
        super().__init__(Window(center_rect(60, 20)), ['Save', 'Cancel'])
        self._target = target
        self._window.set_title(target)

        self._cwd = TextWidget(self.subwin(2, 2, 40, 3))
        self._cwd.set_title('Working Directory')
        self._cwd.set_editable(True)
        self._cwd.set_text(config.local_get_value(target + "_cwd"), True)
        self._cwd.listen('enter', self.on_save)

        self._args = TextWidget(self.subwin(2, 5, 40, 3))
        self._args.set_title('Arguments')
        self._args.set_editable(True)
        self._args.set_text(config.local_get_value(target + "_args"), True)
        self._args.listen('enter', self.on_save)

        self._buttons[0].listen('clicked', self.on_save)
        self.add_widget(self._cwd)
        self.add_widget(self._args)
        self.set_focus(self._cwd)

    def on_save(self):
        config.local_set_value(self._target + "_cwd", self._cwd.text)
        config.local_set_value(self._target + "_args", self._args.text)
        self.close('Save')
