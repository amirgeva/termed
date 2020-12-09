action_list = set()


class FocusTarget:
    def __init__(self):
        for name in dir(self):
            if name.startswith('action_'):
                action_list.add(name[7:])
