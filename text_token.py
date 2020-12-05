class Token:
    def __init__(self, text: str, visual_index: int, text_index: int):
        self.text = text
        self.visual_index = visual_index
        self.text_index = text_index
        self.color = 0
        self.blank = (text.count(' ') == len(text))

    def clone(self):
        res = Token(self.text, self.visual_index, self.text_index)
        res.color = self.color
        return res

    def move(self, delta_visual: int):
        self.visual_index += delta_visual
        return self
