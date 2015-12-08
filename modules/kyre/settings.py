from os import path
import yaml


def load_settings(settings_files):
    """
    Settings are specified as a list of json files
    :param settings_files: List of filenames to load
    :type settings_files: list[str]
    :return: Kyre is run on the combination of all files
    :rtype dict:
    """
    settings_raw = []
    for filename in settings_files:
        if path.exists(filename):
            with open(filename, 'r') as f:
                settings_raw.append(f.read())

    for settings in yaml.load_all('\n'.join(settings_raw)):
        yield settings
