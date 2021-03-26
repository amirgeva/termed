from base import Base

action_list = set()


class FocusTarget(Base):
    def __init__(self):
        super().__init__()
        self.add(self)

    @staticmethod
    def add(obj):
        for name in dir(obj):
            if name.startswith('action_'):
                action_list.add(name[7:])
