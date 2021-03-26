from utils import call_by_name


class Base:
    def __init__(self):
        pass

    def on_action(self, action):
        func_name = f'action_{action}'
        return call_by_name(self, func_name)

