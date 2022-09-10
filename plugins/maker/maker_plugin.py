import os
import subprocess as sp
import config
from plugin import Plugin
from logger import logwrite
import threading


# import time


class MakerPlugin(Plugin):
    def __init__(self):
        super().__init__()
        self._root = os.path.join(config.work_dir, 'build')
        self._offset = 0
        self._output_lines = []
        self._stdout_thread = None
        self._stderr_thread = None
        self._terminate = False

    def _output_loop(self, os):
        output = config.get_app().get_plugin('output')
        for line in os:
            if self._terminate:
                break
            if isinstance(line, bytes):
                line = line.decode('utf-8')
            output.add_text(line.rstrip())

    def _execute(self, args):
        self._terminate = False
        output = config.get_app().get_plugin('output')
        output.clear()
        # if self._output_thread is None:
        #    self._output_thread = threading.Thread(target=self._output_loop)
        #    self._output_thread.start()
        p = sp.Popen(args, stdout=sp.PIPE, stderr=sp.PIPE, cwd=self._root)
        self._stdout_thread = threading.Thread(target=self._output_loop, args=(p.stdout,))
        self._stderr_thread = threading.Thread(target=self._output_loop, args=(p.stderr,))
        self._stdout_thread.start()
        self._stderr_thread.start()
        self._stdout_thread.join()
        self._stderr_thread.join()
        # self._terminate = True
        # self._output_thread = None
        self._stdout_thread = None
        self._stderr_thread = None

    def global_action_configure(self):
        return self.action_configure()

    def action_configure(self):
        output = config.get_app().get_plugin('output')
        try:
            os.makedirs(self._root)
        except FileExistsError:
            pass
        try:
            self._execute(['cmake', '-DCMAKE_BUILD_TYPE=Debug', '-GNinja', '..'])
            self.action_make()
        except FileNotFoundError:
            output.add_text('Failed to configure')

    def global_action_make(self):
        return self.action_make()

    def action_make(self):
        try:
            logwrite(f'Make in {self._root}')
            target = config.local_get_value('target')
            if os.path.exists(os.path.join(self._root, 'Makefile')):
                args = ['make', '-j']
            elif os.path.exists(os.path.join(self._root, 'build.ninja')):
                args = ['ninja']
            else:
                output = config.get_app().get_plugin('output')
                output.clear()
                output.add_text('No build system found')
                return
            if target:
                args.append(target)
            self._execute(args)
        except FileNotFoundError:
            self.action_configure()
