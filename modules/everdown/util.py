import unicodedata
import re
from os import path
import os
from evernote.edam.error.ttypes import EDAMSystemException, EDAMErrorCode
from time import sleep
from logging import getLogger
log = getLogger(__name__)


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


def protect_rate_limit(f, *args, **kwargs):
    while True:
        try:
            return f(*args, **kwargs)
        except EDAMSystemException as e:
            if e.errorCode == EDAMErrorCode.RATE_LIMIT_REACHED:
                duration = e.rateLimitDuration + 5
                log.warning('Evernote API limit reached, sleeping {} seconds'.format(duration))
                sleep(duration)
            else:
                raise e
