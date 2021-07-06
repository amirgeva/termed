from window import Window
from dialogs.dialog import FormDialog
from dialogs.text_widget import TextWidget
from dialogs.wlist import ListWidget
from utils import center_rect
from color import Color
import config


class ColorDialog(FormDialog):
    def __init__(self):
        super().__init__(Window(center_rect(60, 20)), ['Close'])
        self._current_pair = 0
        self._pair_list = ListWidget(self.subwin(2, 2, 18, 14))
        self._pair_list.set_title('Palette')
        self.add_widget(self._pair_list)
        self.sample = TextWidget(self.subwin(22, 3, 10, 1))
        self.sample.set_color(0)
        self.sample.set_text('Sample')
        self.sample.disable_border()
        self.add_widget(self.sample)
        for i in range(1, 16):
            name = f'Pair {i}'
            for field in dir(Color):
                value = getattr(Color, field)
                if isinstance(value, int) and value == i:
                    name = field
                    break
            self._pair_list.add_item(name)
            # sample = TextWidget(self.subwin(22, 3 + i, 10, 1))
        self._pair_list.listen('selection_changed', self._set_current_pair)

        from config import get_app
        self._query = get_app().query_colors
        self._foreground_list = ListWidget(self.subwin(35, 2, 10, 10))
        self._foreground_list.set_title('Fore')
        self._foreground_list.listen('selection_changed', self._change_fore)
        for name in get_app().get_color_names():
            self._foreground_list.add_item(name)
        self.add_widget(self._foreground_list)

        self._background_list = ListWidget(self.subwin(47, 2, 10, 10))
        self._background_list.set_title('Back')
        self._background_list.listen('selection_changed', self._change_back)
        for name in get_app().get_color_names():
            self._background_list.add_item(name)
        self.add_widget(self._background_list)
        self._set_current_pair()

        self.set_focus(self._pair_list)

    def _set_current_pair(self):
        self._current_pair = self._pair_list.get_selection()[1] + 1
        pair = self._query(self._current_pair)
        self._foreground_list.set_selection(pair[0])
        self._background_list.set_selection(pair[1])
        self.sample.set_color(self._current_pair)

    def _change_fore(self):
        c = self._foreground_list.get_selection()[1]
        config.set_value(f'fg{self._current_pair}', c)
        config.get_app().update_color(self._current_pair)

    def _change_back(self):
        c = self._background_list.get_selection()[1]
        config.set_value(f'bg{self._current_pair}', c)
        config.get_app().update_color(self._current_pair)
