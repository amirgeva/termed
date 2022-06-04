import os
import subprocess as sp
import config
from plugin import Plugin
from logger import logwrite
import threading
import time


class MakerPlugin(Plugin):
    def __init__(self):
        super().__init__()
        self._root = os.path.join(config.work_dir, 'build')
        self._offset = 0
        self._output_lines = []
        self._output_thread = None
        self._terminate = False

    def _output_loop(self):
        output = config.get_app().get_plugin('output')
        while not self._terminate:
            if len(self._output_lines) == 0:
                time.sleep(0.1)
            else:
                output.add_text('\n'.join(self._output_lines))
                self._output_lines = []

    def _execute(self, args):
        self._terminate = False
        output = config.get_app().get_plugin('output')
        output.clear()
        if self._output_thread is None:
            self._output_thread = threading.Thread(target=self._output_loop)
            self._output_thread.start()
        p = sp.Popen(args, stdout=sp.PIPE, stderr=sp.STDOUT, cwd=self._root)
        for line in p.stdout:
            text = line.decode('utf-8').rstrip()
            self._output_lines.append(text)
        self._terminate = True
        self._output_thread = None

    def global_action_configure(self):
        return self.action_configure()

    def action_configure(self):
        output = config.get_app().get_plugin('output')
        try:
            os.makedirs(self._root)
        except FileExistsError:
            pass
        try:
            self._execute(['cmake', '..'])
            self.action_make()
        except FileNotFoundError:
            output.add_text('Failed to configure')

    def global_action_make(self):
        return self.action_make()

    def action_make(self):
        try:
            logwrite(f'Make in {self._root}')
            self._execute(['make', '-j'])
        except FileNotFoundError:
            self.action_configure()
