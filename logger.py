from io import TextIOWrapper
from typing import Optional

import config

Logger: Optional[TextIOWrapper] = None


def init_logger():
    global Logger
    if config.logging:
        Logger = open('termed.log', 'w')


def logwrite(s):
    if config.logging:
        if not Logger:
            init_logger()
        if not isinstance(s, str):
            s = str(s)
        Logger.write(s)
        Logger.write('\n')
        Logger.flush()
