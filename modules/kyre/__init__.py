from execution import setup_execution, execute
from settings import load_settings
from dependency import inject


def execute_files(settings_files):
    for settings in load_settings(settings_files):
        execute(settings)
