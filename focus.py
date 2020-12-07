import inspect

action_list = set()


class FocusTarget:
    def __init__(self):
        for name in dir(self):
            try:
                s = inspect.signature(getattr(self, name))
                if f'{s}' == '(flags)':
                    action_list.add(name)
            except TypeError:
                pass
            except ValueError:
                pass
