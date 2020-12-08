from focus import FocusTarget
from dialogs.widget import Widget


class Dialog(FocusTarget):
    def __init__(self, win):
        super().__init__()
        self.window = win
        self.widgets = []
        self.focus: Widget
        self.focus = None

    def add_widget(self, w: Widget):
        self.widgets.append(w)
        w.set_parent(self)
        if self.focus is None:
            self.focus = w

    def render(self):
        self.window.render()
        for w in self.widgets:
            if w is not self.focus:
                w.render()
        if self.focus is not None:
            self.focus.render()

    def change_focus(self, d):
        if self.focus is None:
            return
        try:
            i = self.widgets.index(self.focus)
            self.focus.on_leave_focus()
            i = (i + d) % len(self.widgets)
            self.focus = self.widgets[i]
            self.focus.on_focus()
        except ValueError:
            pass

    def on_action(self, action, flags):
        if self.focus is not None:
            if action == 'tab':
                self.change_focus(1)
            elif action == 'btab':
                self.change_focus(-1)
            else:
                if hasattr(self.focus, action):
                    f = getattr(self.focus, action)
                    f(flags)

    def process_key(self, key):
        if self.focus is not None and hasattr(self.focus, 'process_key'):
            self.focus.process_key(key)
