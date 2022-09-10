import os
import atexit
import json
from typing import List
from utils import ctrl
from configparser import ConfigParser

SHIFTED = 1
END_OF_WORD = 2
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


def get_section(name: str):
    if name not in cfg:
        cfg[name] = {}
    return cfg[name]


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


def local_get_value(name, default=''):
    if name not in local_section:
        local_section[name] = default
    return local_section.get(name)


def local_get_int(name, default=0):
    return int(local_get_value(name, str(default)))


def local_get_bool(name, default=False):
    return local_get_value(name, str(default)) != 'False'


def local_set_value(name, value):
    local_section[name] = str(value)


def save_cfg():
    with open(local_cfg_path, 'w') as f:
        local_cfg.write(f)
    with open(cfg_path, 'w') as f:
        cfg.write(f)


Terminate = False


def terminate_threads():
    global Terminate
    Terminate = True


class Constants:
    def __init__(self):
        self.values = {'TABSIZE': get_int('TABSIZE', 4)}
        self.create_fields()

    def create_fields(self):
        for field in sorted(self.values.keys()):
            if isinstance(field, str):
                setattr(self, field, self.values.get(field))


home = os.environ['HOME']
logging = False
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
    with open(keymap_path) as fi:
        keymap = json.load(fi)
else:
    keymap = generate_default_keymap(keymap_path)
work_dir = os.getcwd()
local_cfg_path = os.path.join(work_dir, '.termed.ini')
local_cfg = ConfigParser()
if os.path.exists(local_cfg_path):
    local_cfg.read(local_cfg_path)
if 'config' not in local_cfg:
    local_cfg['config'] = {}
local_section = local_cfg['config']

atexit.register(terminate_threads)
atexit.register(save_cfg)

const = Constants()


def assign_key(key, action):
    keymap[key] = action


def save_keymap():
    with open(keymap_path, 'w') as fo:
        json.dump(keymap, fo, indent=4)


def get_assigned_key(action) -> str:
    for key in sorted(keymap.keys()):
        key_action = keymap.get(key)
        if action == key_action:
            return key
    return ''


def create_plugin(name: str):
    import importlib
    try:
        m = importlib.__import__(f'plugins.{name}')
        m = getattr(m, name)
        f = getattr(m, 'create')
        return f()
    except ModuleNotFoundError:
        return None


def get_installed_plugins() -> List[str]:
    try:
        plugins_dir = os.path.join(os.path.dirname(__file__), 'plugins')
        files = os.listdir(plugins_dir)
        files = [f for f in files if os.path.isdir(os.path.join(plugins_dir, f))]
        files = [f for f in files if os.path.exists(os.path.join(plugins_dir, f, '__init__.py'))]
        return files
    except FileNotFoundError:
        return []
