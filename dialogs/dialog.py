from focus import FocusTarget


class Dialog(FocusTarget):
    def __init__(self, win):
        super().__init__()
        self.window = win
        self.widgets = []
        self.focus = None

    def add_widget(self, w):
        self.widgets.append(w)

    def render(self):
        for w in self.widgets:
            if w is not self.focus:
                w.render()
        if self.focus is not None:
            self.focus.render()

    def on_action(self, action, flags):
