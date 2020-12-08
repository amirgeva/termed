from dialogs.widget import Widget
# from config import get_app


class ListWidget(Widget):
    def __init__(self, win):
        super().__init__(win)
        self.items = []
        self.offset = 0
        self.cur = 0

    def add_item(self, item):
        self.items.append(item)

    def render(self):
        super().render()
        for y in range(self.window.height()):
            i = y + self.offset
            self.window.set_cursor(0, y)
            w = self.window.width()
            text = ' ' * w
            if i < len(self.items):
                text = self.items[i]
            self.window.set_color(0 if i != self.cur else 1)
            if len(text) > w:
                text = text[0:w]
            if len(text) < w:
                text = text + ' ' * (w - len(text))
            self.window.text(text)

    def move_down(self, flags):
        self.cur += 1
        if self.cur >= len(self.items):
            self.cur = 0

    def move_up(self, flags):
        self.cur -= 1
        if self.cur < 0:
            self.cur = len(self.items) - 1
