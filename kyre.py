#!./.env/bin/python

import os
import sys
import collections
from os import path
import json
import importlib
import re
import shlex
import logging
sys.path.append(os.path.dirname(__file__))
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)
log = logging.getLogger(__name__)


def load_settings(settings_files):
    """
    Settings are specified as a list of json files
    :param settings_files: List of filenames to load
    :type settings_files: list[str]
    :return: Kyre is run on the combination of all files
    :rtype dict:
    """
    settings = {}
    for filename in settings_files:
        if path.exists(filename):
            with open(filename, 'r') as f:
                combine_settings(settings, json.load(f))
    return settings


def combine_settings(d, u):
    """
    Files are combined in order, to full depth
    This can be used to separate the secrets into another file
    >>> combine_settings({
    ...     "sequence": [
    ...         "sequence item"
    ...     ],
    ...     "secret": {
    ...         "comment": "these values elsewhere"
    ...     }
    ... }, {
    ...     "secret": {
    ...         "name": "secret value"
    ...     }
    ... })
    ...
    {'secret': {'comment': 'these values elsewhere', 'name': 'secret value'}, 'sequence': ['sequence item']}

    :rtype dict:
    """
    for k, v in u.iteritems():
        if isinstance(v, collections.Mapping):
            r = combine_settings(d.get(k, {}), v)
            d[k] = r
        else:
            d[k] = u[k]
    return d


# Clever code is not good code. This is bad code, but oh so fun to write.
def dereference_settings(full_tree, partial_tree=None):
    """
    Setting values can reference other settings by referring to their keys
    >>> settings = {
    ...     "reference": "{{other}}",
    ...     "other": "value"
    ... }
    >>> dereference_settings(settings)
    >>> settings
    nothing

    :return: Kyre is run on the result with all references replaced with their respective values
    """
    if partial_tree is None:
        partial_tree = full_tree
    # Look for keys that match "{{anything}}"
    replacement_pattern = re.compile("^{{(.*)}}$")
    insertion_pattern = re.compile("{{(.*)}}")
    for key, value in partial_tree.iteritems():
        if isinstance(value, basestring):
            # If the replacement pattern is found with no leading or trailing characters lookup and replace the value
            replace = replacement_pattern.match(value)
            if replace is not None:
                # If replace matches then replace the result with the looked up value
                partial_tree[key] = lookup_match(replace, full_tree, key, value)
            else:
                # If replace doesn't match attempt to replace occurrences in a larger string
                insertion_pattern.sub(lambda match: lookup_match(match, full_tree, key, value, force_string=True), value)

        elif isinstance(value, collections.Mapping):
            # If the value is a mapping/dict then recurse and check it too
            dereference_settings(full_tree, value)

        elif isinstance(value, list):
            # Convert a list to a dict of 0 indexed keys
            # This is transparent to the lookup_match function because indexing a list and a number-indexed dict is
            # indistinguishable, ex: [1,2,3][0] == {0:1, 1:2, 2:3}[0]
            dereference_settings(full_tree, dict(enumerate(value)))


def lookup_match(match, full_tree, key, value, force_string=False):
    """
    Matches can either be replacements or insertions.
    If the whole value is a reference then it will be replaced, such as including an entire settings tree
    TODO: Example
    If the reference is only part of the string then the references will be replaced.
    :return: A combined
    """
    # Extract the bit between the curly braces
    keystr = match.group(1)

    # Split the keystr on dots, respecting quotes
    lexer = shlex.shlex(keystr)
    lexer.whitespace = '.'
    lexer.whitespace_split = True

    # Get all tokens from lexer, stripping quotes
    keys = [s.strip('\'"') for s in lexer]

    # Lookup the value from settings by a list of keys
    try:
        # http://stackoverflow.com/questions/14692690/access-python-nested-dictionary-items-via-a-list-of-keys
        result = reduce(lambda d, k: d[k], keys, full_tree)
        if force_string:
            # Since it makes sense to replace in a value then convert them
            if isinstance(result, int) or isinstance(result, float) or isinstance(result, long):
                result = str(result)

            if not isinstance(result, basestring):
                log.warning("Reference {} refers to a non-string value, not inserting".format(value))
                return value

        return result
    except KeyError:
        log.warning("Unmatched reference: {}".format(value))
        return value


if __name__ == '__main__':
    settings = load_settings(['avalarky.report.kyre', 'avalarky.report.secret.kyre'])
    dereference_settings(settings)

    assert 'sequence' in settings
    for item in settings['sequence']:
        assert 'module' in item
        assert 'settings' in item
        module = importlib.import_module(item['module'])
        assert 'run' in module.__dict__
        module.run(item['settings'])