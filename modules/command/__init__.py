from ..kyre import execute
import sys


def execute_list(execution_list):
    for execution in execution_list:
        execute(execution)

defined_commands = {}


def add(name, run):
    global defined_commands
    defined_commands[name] = run
    if name in sys.argv:
        execute_list(run)


def run(commands):
    global defined_commands
    for command in commands:
        if command in defined_commands:
            execute_list(defined_commands[command])
