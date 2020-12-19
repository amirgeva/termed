action_list = set()


class FocusTarget:
    def __init__(self):
        self.add(self)

    @staticmethod
    def add(obj):
        for name in dir(obj):
            if name.startswith('action_'):
                action_list.add(name[7:])
