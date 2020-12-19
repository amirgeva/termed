from typing import List
from window import Window
from dialogs.dialog import FormDialog
from dialogs.text_widget import TextWidget
from utils import center_rect


class PromptDialog(FormDialog):
    def __init__(self, title: str, question: str, buttons: List[str]):
        super().__init__(Window(center_rect(60, 10)), buttons)
        self._window.set_title(title)
        self.question = TextWidget(self.subwin(3, 2, 50, 3))
        self.question.disable_border()
        self.question.set_text(question)
        self.add_widget(self.question)

