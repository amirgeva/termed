from typing import List
import functools
from geom import Rect
from config import assign_key, save_keymap, get_assigned_key
from window import Window
from dialogs.dialog import Dialog
from dialogs.wlist import ListWidget
from dialogs.button import Button
from dialogs.text_widget import TextWidget
from dialogs.key_widget import KeyWidget
from utils import center_rect


class KeymapDialog(Dialog):
    def __init__(self, title: str, question: str, buttons: List[str]):
        super().__init__(Window(center_rect(60, 10)))
        self.result=''
        self._window.set_title(title)
        self.question = TextWidget(self.subwin(3, 3, 50, 3))
        self.question.set_text(question)
        x=3
        for button_text in buttons:
            button = Button(self.subwin(x,7,12,3), button_text)
            button.listen('clicked',functools.partial(self.clicked, button_text))
            x+=15

    def clicked(self, button_text):
        self.result = button_text
