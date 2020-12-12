class Token:
    def __init__(self, text: str, visual_index: int, text_index: int):
        self._text = text
        self._visual_index = visual_index
        self._text_index = text_index
        self._color = 0
        self._blank = (text.count(' ') == len(text))

    def __len__(self):
        return len(self._text)

    def clone(self):
        res = Token(self._text, self._visual_index, self._text_index)
        res._color = self._color
        res._blank = self._blank
        return res

    def move(self, delta_visual: int):
        self._visual_index += delta_visual
        return self

    def append_text(self, text):
        self._text += text

    def get_visual_index(self):
        return self._visual_index

    def get_text(self):
        return self._text

    def get_text_index(self):
        return self._text_index

    def get_color(self):
        return self._color

    def is_blank(self):
        return self._blank

    def set_visual_index(self, v: int):
        self._visual_index = v

    def set_text(self, text: str):
        self._text = text

    def set_color(self, color: int):
        self._color = color

    def get_right_part(self, n: int):
        return Token(self.get_text()[n:], self.get_visual_index() + n, self.get_text_index() + n)
