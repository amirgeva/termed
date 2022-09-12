import pyperclip

data=['']
use_pyperclip=False
try:
    pyperclip.copy("test")
    use_pyperclip=True
except Exception:
    pass


def copy(text: str):
    if use_pyperclip:
        pyperclip.copy(text)
    else:
        data[0]=text

def paste():
    if use_pyperclip:
        return pyperclip.paste()
    else:
        return data[0]


