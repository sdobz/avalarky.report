from evernote.api.client import EvernoteClient
from evernote.edam.error.ttypes import EDAMSystemException, EDAMErrorCode
from evernote.edam.notestore.ttypes import NoteFilter, NotesMetadataResultSpec
import fnmatch
import functools
from time import sleep
import re
import logging
log = logging.getLogger(__name__)


def glob_to_regex(glob):
    return re.compile(fnmatch.translate(glob))


def memoize(f):
    f.__cache = None

    @functools.wraps(f)
    def memoizer(*args, **kwargs):
        if f.__cache is None:
            f.__cache = f(*args, **kwargs)
        return f.__cache
    return memoizer


def rate_limit(f):
    """
    Add a try catch to repeatedly try the function until it no longer experiences a rate limit problem
    Warning: Can run a function multiple times, ensure it is idempotent.
    :param f:
    :return:
    """
    def rate_limit_inner(*args, **kwargs):
        while True:
            try:
                return f(*args, **kwargs)
            except EDAMSystemException as e:
                if e.errorCode == EDAMErrorCode.RATE_LIMIT_REACHED:
                    duration = e.rateLimitDuration + 2
                    log.warning('Evernote API limit reached, sleeping {} seconds'.format(duration))
                    sleep(duration)
                else:
                    raise e
    return rate_limit_inner


class Everfetch(object):
    def __init__(self, token, token_sandbox, sandbox):
        self.token = token if not sandbox else token_sandbox
        self.client = EvernoteClient(token=token, sandbox=sandbox)

    @memoize
    @rate_limit
    def note_store(self):
        """
        :rtype evernote.edam.notestore.NoteStore:
        :return: The note store related to the token
        """
        return self.client.get_note_store()

    def fetch_note_metadata(self, notebooks):
        for notebook in self.fetch_notebooks(notebooks):
            for note_metadata in self.fetch_note_metadata_from_notebook(notebook):
                yield {
                    'metadata': note_metadata
                }

    @memoize
    @rate_limit
    def fetch_all_notebooks(self):
        return self.note_store().listNotebooks(self.token)

    def fetch_notebooks(self, notebook_globs):
        notebook_regexs = [glob_to_regex(glob) for glob in notebook_globs]

        for notebook in self.fetch_all_notebooks():
            for regex in notebook_regexs:
                if regex.match(notebook.name):
                    yield notebook

    def fetch_note_metadata_from_notebook(self, notebook):
        updated_filter = NoteFilter(notebookGuid=notebook.guid)
        result_spec = NotesMetadataResultSpec(includeUpdated=True)
        offset = 0
        max_notes = 10
        while True:
            note_results = self.fetch_note_metadata_batch(updated_filter, offset, max_notes, result_spec)
            for note_metadata in note_results.notes:
                yield note_metadata

            offset += max_notes
            if offset > note_results.totalNotes:
                break

    @rate_limit
    def fetch_note_metadata_batch(self, updated_filter, offset, max_notes, result_spec):
        return self.note_store().findNotesMetadata(self.token, updated_filter, offset, max_notes, result_spec)

