import unicodedata
import re
from os import path
import os


def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.
    """
    value = unicode(value)
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = unicode(re.sub('[^\w\s-]', '', value).strip().lower())
    return unicode(re.sub('[-\s]+', '-', value))


def ensure_dir(filename):
    dir = path.dirname(filename)
    if not path.exists(dir):
        os.makedirs(dir, mode=0755)
