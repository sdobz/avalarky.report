from pelican.settings import DEFAULT_CONFIG, configure_settings
from pelican import Pelican
import copy


def combine(d1, d2):
    d3 = copy.deepcopy(d1)
    d3.update(d2)
    return d3


def initialize_settings(settings):
    # This initializes settings according to pelican
    return configure_settings(combine(DEFAULT_CONFIG, settings))


def run(**settings):
    Pelican(initialize_settings(settings)).run()
