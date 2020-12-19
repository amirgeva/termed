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
        'KEY_LEFT': 'move_left',
        'KEY_RIGHT': 'move_right',
        'KEY_DOWN': 'move_down',
        'KEY_UP': 'move_up',
        'KEY_PPAGE': 'move_pgup',
        'KEY_NPAGE': 'move_pgdn',
        'KEY_HOME': 'move_home',
        'KEY_END': 'move_end',
        'kLFT5': 'move_word_left',
        'kRIT5': 'move_word_right',
        'KEY_BTAB': 'backtab',

        'KEY_SLEFT': 'select_left',
        'KEY_SRIGHT': 'select_right',
        'KEY_SF': 'select_down',
        'KEY_SR': 'select_up',
        'KEY_SPREVIOUS': 'select_pgup',
        'KEY_SNEXT': 'select_pgdn',
        'KEY_SHOME': 'select_home',
        'KEY_SEND': 'select_end',
        'kLFT6': 'select_word_left',
        'kRIT6': 'select_word_right',

        'ESC': 'escape',

        ctrl('C'): 'copy',
        ctrl('F'): 'find',
        ctrl('X'): 'cut',
        ctrl('V'): 'paste',
        ctrl('N'): 'file_new',
        ctrl('S'): 'file_save',
        ctrl('O'): 'file_open',
        ctrl('Q'): 'file_exit',
        ctrl('R'): 'macro_record',
        ctrl('P'): 'macro_play',
        ctrl('Z'): 'undo',

        '\t': 'tab',
        '\n': 'enter'
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
cfg_dir = os.path.join(home, '.termed')
os.makedirs(cfg_dir, 0o755, True)
cfg_path = os.path.join(cfg_dir, 'termed.ini')
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


def assign_key(key, action):
    keymap[key] = action


def save_keymap():
    with open(keymap_path, 'w') as fo:
        json.dump(keymap, fo, indent=4)


def get_assigned_key(action):
    for key in sorted(keymap.keys()):
        key_action = keymap.get(key)
        if action == key_action:
            return key
    return ''
