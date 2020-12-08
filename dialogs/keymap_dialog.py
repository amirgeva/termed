from geom import Point, Rect
from window import Window
from dialogs.dialog import Dialog
from dialogs.wlist import ListWidget
from dialogs.text_widget import TextWidget
from utils import center_rect
from focus import action_list


class KeymapDialog(Dialog):
    def __init__(self):
        super().__init__(Window(center_rect(Point(40, 16))))
        self.action_list = ListWidget(self.window.subwindow(Rect(20, 4, 18, 11)))
        self.action_list.set_title('Actions')
        for item in sorted(list(action_list)):
            self.action_list.add_item(item)
        self.add_widget(self.action_list)
        self.search_text = TextWidget(self.window.subwindow(Rect(20, 1, 18, 3)))
        self.search_text.set_title('Search')
        self.search_text.set_editable(True)
        self.add_widget(self.search_text)
        self.search_text.listen('modified',self.on_search)

    def on_search(self):
        term = self.search_text.text
        self.action_list.clear()
        for item in sorted(list(action_list)):
            if len(term)==0 or term in item:
                self.action_list.add_item(item)
