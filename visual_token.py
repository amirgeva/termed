class VisualToken:
    def __init__(self, pos: int, text: str):
        self._pos = pos
        self._text = text
        self._color = 0

    def set_color(self, color: int):
        self._color = color

    def move(self, dx):
        self._pos += dx

    def clip(self, x0: int, x1: int):
        if x1 <= self._pos:
            self._text = ''
        else:
            right = self._pos + len(self._text)
            if right > x1:
                self._text = self._text[0:(x1 - right)]
            if self._pos < x0:
                idx = x0 - self._pos
                self._pos = x0
                self._text = self._text[idx:]

    def get_pos(self):
        return self._pos

    def get_color(self):
        return self._color

    def get_text(self):
        return self._text
