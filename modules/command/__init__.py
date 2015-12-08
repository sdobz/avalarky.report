from ..kyre import execute
import sys

defined_commands = {}


def add(name, run):
    global defined_commands
    defined_commands[name] = run
    if name in sys.argv:
        execute(run)


def run(*commands):
    global defined_commands
    for command in commands:
        if command in defined_commands:
            execute(defined_commands[command])
