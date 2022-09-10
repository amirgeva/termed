import re
import subprocess as sp
import threading
import os
from dataclasses import dataclass
from typing import Dict, Callable, Optional
from pygdbmi import gdbmiparser
import config


@dataclass
class Breakpoint:
    number: int
    enabled: bool
    path: str
    line: int


class ResultWaiter:
    def __init__(self):
        self._event = threading.Event()
        self._result = None

    def __call__(self, result):
        self._result = result
        self._event.set()

    def wait(self):
        self._event.wait()
        return self._result


class Debugger:
    def __init__(self):
        self._target = config.local_get_value('target')
        self._executable = os.path.join(config.work_dir, 'build', 'Debug', self._target)
        if not os.path.exists(self._executable):
            config.get_app().get_plugin('output').add_text(f'Executable {self._executable} not found')
        self._cwd = config.local_get_value(self._target + "_cwd")
        self._args = config.local_get_value(self._target + "_args")
        args = ['gdb', '--interpreter=mi', '--args', self._executable]
        args.extend(self._args.split())
        self._terminate = False
        self._resumed = False
        self._token = 0
        self._handlers: Dict[int, Callable] = {}
        self._process = sp.Popen(args, stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.PIPE, cwd=self._cwd)
        self._thread = threading.Thread(target=self.stdout_thread)
        self._thread.start()

    def add_breakpoint(self, location: str):
        if not self.is_resumed():
            self._sync_send(f'-break-insert {location}')
            return True
        return False

    def run(self):
        if not self.is_resumed():
            self._sync_send('-exec-run')
            return True
        return False

    def cont(self):
        if not self.is_resumed():
            self._sync_send('-exec-continue')
            return True
        return False

    def next(self):
        if not self.is_resumed():
            self._sync_send('-exec-next')
            return True
        return False

    def step(self):
        if not self.is_resumed():
            self._sync_send('-exec-step')
            return True
        return False

    def until(self, location: str):
        if not self.is_resumed():
            self._sync_send(f'-exec-until {location}')
            return True
        return False

    def is_resumed(self):
        return self._resumed

    def get_all_breakpoints(self):
        if self.is_resumed():
            return []
        result = self._sync_send('-break-list')
        bps = result['payload']['BreakpointTable']['body']
        res = []
        for bp in bps:
            res.append(Breakpoint(int(bp['number']), bp['enabled'] == 'y', bp['fullname'], int(bp['line'])))
        return res

    def stdout_thread(self):
        token_pattern = r'(\d+)'
        for line in self._process.stdout:
            if self._terminate:
                break
            m = re.match(token_pattern, line)
            if m:
                token_text = m.groups()[0]
                token = int(token_text)
                line = line[len(token_text):]
                if token in self._handlers:
                    handler = self._handlers[token]
                    handler(gdbmiparser.parse_response(line))
                    del self._handlers[token]

    def shutdown(self):
        self._terminate = True
        self._send('quit')
        self._thread.join()

    def _generate_token(self):
        self._token += 1
        return self._token

    def _sync_send(self, command: str):
        sync = ResultWaiter()
        self._send(command, sync)
        return sync.wait()

    def _send(self, command: str, handler: Optional[Callable] = None):
        token = self._generate_token()
        if handler:
            self._handlers[token] = handler
        command = str(token) + command + "\n"
        self._process.stdin.write(bytes(command, 'utf-8'))
        return token


def unit_test():
    pass


if __name__ == '__main__':
    unit_test()
