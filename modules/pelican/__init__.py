from horrible_monkey_patch import patch_pelican_settings
from pelican import main as run_pelican


def run(**settings):
    patch_pelican_settings(settings)
    run_pelican()
