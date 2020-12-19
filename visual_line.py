from config import const
from textwrap import TextWrapper

wrapper = TextWrapper(width=1000000000, expand_tabs=True, tabsize=const.TABSIZE, replace_whitespace=True,
                      drop_whitespace=False)


def tab_spaces(pos):
    return const.TABSIZE - (pos % const.TABSIZE)


class VisualLine:
    def __init__(self, text: str = ''):
        self._visual_text = ''
        self._logical_text = ''
        self._tabs = []
        if text:
            self.set_text(text)

    def set_text(self, text: str):
        self._tabs = [i for i, c in enumerate(text) if c == '\t']
        self._logical_text = text
        self._visual_text = wrapper.fill(text)
        extra = 0
        for i in range(len(self._tabs)):
            self._tabs[i] += extra
            spaces = tab_spaces(self._tabs[i])
            extra += spaces - 1

    def insert(self, pos: int, text: str):
        if pos < 0 or pos > self.get_logical_len():
            return False
        self.set_text(self._logical_text[0:pos] + text + self._logical_text[pos:])
        return True

    def append(self, text: str):
        return self.insert(self.get_logical_len(), text)

    def clip_coords(self, pos: int, n: int):
        if pos < 0 or pos >= len(self._logical_text):
            return pos, 0
        right = pos + n
        if right > len(self._logical_text):
            right = len(self._logical_text)
        return pos, right-pos

    def erase(self, pos: int, n: int = 1):
        if pos < 0 or pos >= len(self._logical_text):
            return False
        right = pos + n
        if right > len(self._logical_text):
            right = len(self._logical_text)
        self.set_text(self._logical_text[0:pos] + self._logical_text[right:])
        return True

    def get_logical_len(self):
        return len(self._logical_text)

    def get_logical_text(self):
        return self._logical_text

    def get_visual_len(self):
        return len(self._visual_text)

    def get_visual_text(self):
        return self._visual_text

    def get_visual_index(self, pos: int):
        if pos < 0:
            return -1
        for tab in self._tabs:
            if pos <= tab:
                break
            pos += tab_spaces(tab) - 1
        if pos > len(self._visual_text):
            return -1
        return pos

    def get_logical_index(self, pos: int):
        if pos > len(self._visual_text) or pos < 0:
            return -1
        for tab in reversed(self._tabs):
            if pos > tab:
                spaces = tab_spaces(tab)
                nxt = tab + spaces
                if pos >= nxt:
                    pos -= spaces - 1
                else:
                    pos = tab
        return pos

    def split(self, pos: int):
        if pos < 0 or pos > self.get_logical_len():
            raise RuntimeError("Invalid line split")
        if pos == self.get_logical_len():
            return VisualLine()
        text = self.get_logical_text()
        next_line = VisualLine(text[pos:])
        self.erase(pos, len(text) - pos)
        return next_line

    def extend(self, line):
        if isinstance(line, VisualLine):
            self.set_text(self._logical_text + line.get_logical_text())
        elif isinstance(line, str):
            self.set_text(self._logical_text + line)
        else:
            raise RuntimeError('Invalid type in VisualLine.extend')

    def __repr__(self):
        v = self._visual_text.replace(' ', '@')
        return f'"{self._logical_text}"   "{v}"'
