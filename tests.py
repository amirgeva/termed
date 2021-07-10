#!/usr/bin/env python3
import unittests
import sys
from termcolor import colored


def main():
    modules = [m for m in dir(unittests) if not m.startswith('_')]
    for name in modules:
        try:
            m = getattr(unittests, name)
            test = getattr(m, 'unit_test')
            if test() != 0:
                print(colored(f"Test {name} has failed", 'red'))
                return 1
        except AttributeError:
            pass
    print(colored("All tests passed", 'green'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
