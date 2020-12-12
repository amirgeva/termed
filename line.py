from config import const
from text_token import Token


class Line:
    def __init__(self, text: str):
        self._text = ''
        self._tabs = []
        self._tokens = []
        if text:
            self.set_text(text)

    def size(self):
        return len(self._text)

    def __len__(self):
        return len(self._text)

    def get_text(self):
        return self._text

    def append_text(self, text: str):
        self._text = self._text + text
        if len(self._tokens) > 0:
            if text == '\t':
                self._tabs.append(len(self._text) - 1)
            else:
                self._tokens[-1].append_text(text)
        else:
            self.calc_tokens()

    def insert_text(self, x: int, text: str):
        self.set_text(self._text[0:x] + text + self._text[x:])

    def join(self, line):
        self.set_text(self._text + line.get_text())

    def split(self, x: int):
        text = self._text[x:]
        self.set_text(self._text[0:x])
        return Line(text)

    def insert_char(self, text_index: int, c: str):
        if text_index == len(self._text):
            self.append_text(c)
        else:
            self.set_text(self._text[0:text_index] + c + self._text[text_index:])

    def delete_char(self, x: int):
        self.set_text(self._text[0:x] + self._text[x + 1:])

    def delete_block(self, from_index: int, to_index: int):
        if to_index == -1:
            self.set_text(self._text[0:from_index])
        else:
            self.set_text(self._text[0:from_index] + self._text[to_index:])

    def set_text(self, text: str):
        self._text = text
        self._tabs = []
        for i in range(len(text)):
            if text[i] == '\t':
                self._tabs.append(i)
        self.calc_tokens()

    def calc_tokens(self):
        self._tokens = []
        visual = 0
        text_index = 0
        for tab_index in self._tabs:
            if text_index == tab_index:
                text_index = text_index + 1
                visual = visual + (const.TABSIZE - visual % 4)
            else:
                self._tokens.append(Token(self._text[text_index:tab_index], visual, text_index))
                visual = visual + (tab_index - text_index)
                visual = visual + (const.TABSIZE - visual % 4)
                text_index = tab_index + 1
        if text_index < len(self._text):
            self._tokens.append(Token(self._text[text_index:], visual, text_index))

    def get_token_count(self):
        return len(self._tokens)

    def get_token(self, i: int):
        return self._tokens[i].clone()
