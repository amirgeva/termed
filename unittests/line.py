#!/usr/bin/env python3
from config import const
from visual_line import VisualLine
from termcolor import colored


class TestLine:
    def __init__(self, text: str = ''):
        self._logical_text = ''
        self._visual_text = ''
        self._logical2visual = []
        self._visual2logical = []
        if text:
            self.set_text(text)

    def set_text(self, text: str):
        self._logical_text = text
        self._visual_text = ''
        self._logical2visual = []
        self._visual2logical = []
        for i in range(len(text)):
            self._logical2visual.append(len(self._visual_text))
            c = text[i]
            if c == '\t':
                spaces = const.TABSIZE - (len(self._visual_text) % const.TABSIZE)
                for j in range(spaces):
                    self._visual2logical.append(i)
                self._visual_text += ' ' * spaces
            else:
                self._visual_text += c
                self._visual2logical.append(i)
        self._logical2visual.append(len(self._visual_text))
        self._visual2logical.append(len(self._logical_text))

    def insert(self, pos: int, text: str):
        if pos < 0 or pos > len(self._logical_text):
            return False
        self.set_text(self._logical_text[0:pos] + text + self._logical_text[pos:])
        return True

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
        if 0 <= pos < len(self._logical2visual):
            return self._logical2visual[pos]
        return -1

    def get_logical_index(self, pos: int):
        if 0 <= pos < len(self._visual2logical):
            return self._visual2logical[pos]
        return -1

    def __repr__(self):
        v = self._visual_text.replace(' ', '@')
        return f'"{self._logical_text}"   "{v}"'


def unit_test():
    from random import randint, seed
    seed(1)
    tgt = VisualLine()
    ref = TestLine()
    cases = 100000
    test_case = 0
    while test_case < cases:
        test_case += 1
        # if (test_case%1000)==0:
        #     print(ref)
        action = randint(0, 8)
        n = ref.get_logical_len()
        if action < 2:
            letter = chr(randint(65, 90))
            pos = randint(0, n)
            ref.insert(pos, letter)
            tgt.insert(pos, letter)
        if action == 2 and randint(0, 20) < 4:
            letter = '\t'
            pos = randint(0, n)
            ref.insert(pos, letter)
            tgt.insert(pos, letter)
        if action == 3:
            if n >= 40 or randint(0, 10) < 4:
                pos = randint(0, n)
                ref.erase(pos)
                tgt.erase(pos)
        if action == 4 and n > 50:
            p1 = randint(0, n)
            p2 = randint(10, n)
            if p1 > p2:
                p1, p2 = p2, p1
            ref.erase(p1, p2 - p1)
            tgt.erase(p1, p2 - p1)
        s1 = ref.get_visual_text()
        s2 = tgt.get_visual_text()
        if s1 != s2:
            print(colored("FAILED visual text",'red'))
            s1 = ref.get_visual_text()
            s2 = tgt.get_visual_text()
            print(f'"{s1}" != "{s2}"')
            break
        s1 = ref.get_logical_text()
        s2 = tgt.get_logical_text()
        if s1 != s2:
            print(colored("FAILED Logical text",'red'))
            break
        if action == 8:
            pos = randint(0, 10 + ref.get_visual_len())
            p1 = ref.get_logical_index(pos)
            p2 = tgt.get_logical_index(pos)
            if p1 != p2:
                print(colored("FAILED Logical index",'red'))
                p1 = ref.get_logical_index(pos)
                p2 = tgt.get_logical_index(pos)
                print(f'{p1}!={p2}')
                break
        if action == 9:
            pos = randint(0, 10 + ref.get_logical_len())
            p1 = ref.get_visual_index(pos)
            p2 = tgt.get_visual_index(pos)
            if p1 != p2:
                print(colored("FAILED Visual index",'red'))
                break
    if test_case == cases:
        print(colored("Line test Passed",'green'))
        return 0
    return 1


if __name__ == '__main__':
    import sys
    sys.exit(unit_test())
