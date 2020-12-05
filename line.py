from config import const
from text_token import Token


class Line:
    def __init__(self, text):
        self.text = ''
        self.tabs = []
        self.tokens = []
        if text:
            self.set_text(text)

    def size(self):
        return len(self.text)

    def __len__(self):
        return len(self.text)

    def append_text(self, text):
        self.text = self.text + text
        if len(self.tokens) > 0:
            if text == '\t':
                self.tabs.append(len(self.text) - 1)
            else:
                self.tokens[-1].text += text
        else:
            self.calc_tokens()

    def insert_text(self, x, text):
        self.set_text(self.text[0:x] + text + self.text[x:])

    def join(self, line):
        self.set_text(self.text + line.text)

    def split(self, x):
        text = self.text[x:]
        self.set_text(self.text[0:x])
        return Line(text)

    def insert_char(self, text_index, c):
        if text_index == len(self.text):
            self.append_text(c)
        else:
            self.set_text(self.text[0:text_index] + c + self.text[text_index:])

    def delete_char(self, x):
        self.set_text(self.text[0:x] + self.text[x + 1:])

    def delete_block(self, from_index, to_index):
        self.set_text(self.text[0:from_index] + self.text[to_index:])

    def set_text(self, text):
        self.text = text
        self.tabs = []
        for i in range(len(text)):
            if text[i] == '\t':
                self.tabs.append(i)
        self.calc_tokens()

    def calc_tokens(self):
        self.tokens = []
        visual = 0
        text_index = 0
        for tab_index in self.tabs:
            if text_index == tab_index:
                text_index = text_index + 1
                visual = visual + (const.TABSIZE - visual % 4)
            else:
                self.tokens.append(Token(self.text[text_index:tab_index], visual, text_index))
                visual = visual + (tab_index - text_index)
                visual = visual + (const.TABSIZE - visual % 4)
                text_index = tab_index + 1
        if text_index < len(self.text):
            self.tokens.append(Token(self.text[text_index:], visual, text_index))
