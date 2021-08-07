import os
import subprocess as sp
import config
from plugin import Plugin
from logger import logwrite


class MakerPlugin(Plugin):
    def __init__(self):
        super().__init__()
        self._root = os.path.join(config.work_dir, 'build')
        self._offset = 0

    def global_action_make(self):
        return self.action_make()

    def action_make(self):
        logwrite(f'Make in {self._root}')
        output = config.get_app().get_plugin('output')
        output.clear()
        p = sp.Popen(['make'], stdout=sp.PIPE, stderr=sp.STDOUT, cwd=self._root)
        for line in p.stdout:
            text = line.decode('utf-8').rstrip()
            output.add_text(text)
