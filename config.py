import os
import atexit
import json
from utils import ctrl
from configparser import ConfigParser

SHIFTED = 1
app = None


def get_app():
    return app


def generate_default_keymap(path: str):
    mapping = {
        'KEY_LEFT': ['move_left', 0],
        'KEY_RIGHT': ['move_right', 0],
        'KEY_DOWN': ['move_down', 0],
        'KEY_UP': ['move_up', 0],
        'KEY_PPAGE': ['move_pgup', 0],
        'KEY_NPAGE': ['move_pgdn', 0],
        'KEY_HOME': ['move_home', 0],
        'KEY_END': ['move_end', 0],
        'kLFT5': ['move_word_left', 0],
        'kRIT5': ['move_word_right', 0],

        'KEY_SLEFT': ['move_left', SHIFTED],
        'KEY_SRIGHT': ['move_right', SHIFTED],
        'KEY_SF': ['move_down', SHIFTED],
        'KEY_SR': ['move_up', SHIFTED],
        'KEY_SPREVIOUS': ['move_pgup', SHIFTED],
        'KEY_SNEXT': ['move_pgdn', SHIFTED],
        'KEY_SHOME': ['move_home', SHIFTED],
        'KEY_SEND': ['move_end', SHIFTED],
        'kLFT6': ['move_word_left', SHIFTED],
        'kRIT6': ['move_word_right', SHIFTED],

        ctrl('C'): ['copy', 0],
        ctrl('F'): ['find', 0],
        ctrl('X'): ['cut', 0],
        ctrl('V'): ['paste', 0],
        ctrl('N'): ['new_file', 0],
        ctrl('S'): ['save_file', 0],
        ctrl('O'): ['open_file', 0],
        ctrl('Q'): ['quit', 0],
        ctrl('R'): ['record_macro', 0],
        ctrl('P'): ['play_macro', 0],
        ctrl('Z'): ['undo', 0],
    }
    with open(path, 'w') as fo:
        json.dump(mapping, fo, indent=4)
    return mapping


def get_value(name, default=''):
    if name not in section:
        section[name] = default
    return section.get(name)


def get_int(name, default=0):
    return int(get_value(name, str(default)))


def get_bool(name, default=False):
    return get_value(name, str(default)) != 'False'


def set_value(name, value):
    section[name] = str(value)


def save_cfg():
    with open(cfg_path, 'w') as configfile:
        cfg.write(configfile)


class Constants:
    def __init__(self):
        self.values = {'TABSIZE': get_int('TABSIZE', 4)}
        self.create_fields()

    def create_fields(self):
        for field in sorted(self.values.keys()):
            if isinstance(field, str):
                setattr(self, field, self.values.get(field))


home = os.environ['HOME']
cfg_dir = os.path.join(home, '.ted')
os.makedirs(cfg_dir, 0o755, True)
cfg_path = os.path.join(cfg_dir, 'ted.ini')
keymap_path = os.path.join(cfg_dir, 'keymap.json')
cfg = ConfigParser()
cfg.read(cfg_path)
if 'config' not in cfg:
    cfg['config'] = {}
section = cfg['config']
if os.path.exists(keymap_path):
    with open(keymap_path) as f:
        keymap = json.load(f)
else:
    keymap = generate_default_keymap(keymap_path)

atexit.register(save_cfg)

const = Constants()
