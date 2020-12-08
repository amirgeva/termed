from config import get_app
from geom import Point, Rect
from window import Window
from dialogs.dialog import Dialog
from dialogs.wlist import ListWidget
from utils import center_rect
from focus import action_list


class KeymapDialog(Dialog):
    def __init__(self):
        super().__init__(Window(center_rect(Point(40, 16))))
        self.action_list = ListWidget(self.window.subwindow(Rect(20, 2, 18, 12)))
        for item in sorted(list(action_list)):
            self.action_list.add_item(item)
        self.add_widget(self.action_list)
