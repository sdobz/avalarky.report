from boto.s3.connection import S3Connection
from boto.s3.key import Key
import os
import logging
import ssl
log = logging.getLogger(__name__)


def monkey_patch_ssl():
    _old_match_hostname = ssl.match_hostname

    def _new_match_hostname(cert, hostname):
        if hostname.endswith('.s3.amazonaws.com'):
            pos = hostname.find('.s3.amazonaws.com')
            hostname = hostname[:pos].replace('.', '') + hostname[pos:]
        return _old_match_hostname(cert, hostname)

    ssl.match_hostname = _new_match_hostname


def upload(settings, source):
    monkey_patch_ssl()
    s3 = S3Connection(settings['access-key-id'], settings['secret-access-key'])
    bucket = s3.get_bucket(settings['bucket'])
    for path, dir, files in os.walk(source):
        for file in files:
            relpath = os.path.relpath(os.path.join(path, file))
            k = Key(bucket)
            k.key = relpath[len(source)+1:]
            k.set_contents_from_filename(relpath)
            k.set_acl('public-read')
            log.info('S3: Uploaded {}'.format(file))
