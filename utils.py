class ExitException(Exception):
    pass


def count_leading_spaces(s):
    n = 0
    for c in s:
        if c != ' ':
            break
        n += 1
    return n


def align(s, n):
    if len(s) > n:
        return s[0:n]
    if len(s) < n:
        return s + ' ' * (n - len(s))
    return s


def ctrl(key):
    return chr(ord(key) - ord('A') + 1)
