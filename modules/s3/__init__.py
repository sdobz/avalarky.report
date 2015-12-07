from boto.s3.connection import S3Connection
from boto.s3.key import Key
import os
import ssl
import hashlib
import logging
log = logging.getLogger(__name__)


def monkey_patch_ssl():
    if not hasattr(ssl, 'match_hostname'):
        return
    _old_match_hostname = ssl.match_hostname

    def _new_match_hostname(cert, hostname):
        if hostname.endswith('.s3.amazonaws.com'):
            pos = hostname.find('.s3.amazonaws.com')
            hostname = hostname[:pos].replace('.', '') + hostname[pos:]
        return _old_match_hostname(cert, hostname)

    ssl.match_hostname = _new_match_hostname


def file_hash(f):
    return hashlib.md5(open(f, 'rb').read()).hexdigest()


def upload(**settings):
    monkey_patch_ssl()
    s3 = S3Connection(settings['access-key-id'], settings['secret-access-key'])
    bucket = s3.get_bucket(settings['bucket'])
    source = settings['source']
    for path, dir, files in os.walk(source):
        for file in files:
            relpath = os.path.relpath(os.path.join(path, file))
            key_str = relpath[len(source)+1:]
            key = bucket.get_key(key_str)
            if key is None or file_hash(relpath) != key.etag.strip('"'):
                k = Key(bucket)
                k.key = key_str
                k.set_contents_from_filename(relpath)
                k.set_acl('public-read')
                log.info('S3: Uploaded {}'.format(file))
            else:
                log.info('S3: Skipped {}'.format(file))

    for key in bucket.list():
        local_filename = os.path.join(source, key.key)
        if not os.path.exists(local_filename):
            bucket.delete_key(key.key)
            log.info('{} does not exist locally, removed from s3'.format(key.key))
