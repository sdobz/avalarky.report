import json
import collections
from os import path


def update(d, u):
    for k, v in u.iteritems():
        if isinstance(v, collections.Mapping):
            r = update(d.get(k, {}), v)
            d[k] = r
        else:
            d[k] = u[k]
    return d


def load_settings(settings_files):
    settings = {}
    for filename in settings_files:
        if path.exists(filename):
            with open(filename, 'r') as f:
                update(settings, json.load(f))
    return settings
