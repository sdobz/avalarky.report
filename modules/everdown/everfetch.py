from evernote.api.client import EvernoteClient
from evernote.edam.error.ttypes import EDAMSystemException, EDAMErrorCode
from evernote.edam.notestore.ttypes import NoteFilter, NotesMetadataResultSpec
import fnmatch
import functools
from ..kyre.execution import get_context
from time import sleep
from util import slugify
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
    def __init__(self, token, token_sandbox, sandbox, notebooks):
        self.token = token if not sandbox else token_sandbox
        self.client = EvernoteClient(token=token, sandbox=sandbox)
        self.notebooks = notebooks

    @memoize
    @rate_limit
    def note_store(self):
        """
        :rtype evernote.edam.notestore.NoteStore:
        :return: The note store related to the token
        """
        return self.client.get_note_store()

    @memoize
    @rate_limit
    def fetch_all_notebooks(self):
        return self.note_store().listNotebooks(self.token)

    @rate_limit
    def fetch_note_metadata_page(self, updated_filter, offset, max_notes, result_spec):
        return self.note_store().findNotesMetadata(self.token, updated_filter, offset, max_notes, result_spec)

    @memoize
    def fetch_note(self, note_guid):
        return self.note_store().getNote(
            authentication_token=self.token,
            guid=note_guid,
            withContent=True,
            withResourcesData=False,
            withResourcesRecognition=False,
            withResourcesAlternateData=False)

    def fetch_note_metadata(self, notebooks):
        for notebook in self.fetch_notebooks(notebooks):
            for note_metadata in self.fetch_note_metadata_from_notebook(notebook):
                yield note_metadata

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
            note_results = self.fetch_note_metadata_page(updated_filter, offset, max_notes, result_spec)
            for note_metadata in note_results.notes:
                yield note_metadata

            offset += max_notes
            if offset > note_results.totalNotes:
                break

    def __iter__(self):
        for note_metadata in self.fetch_note_metadata(self.notebooks):
            yield RemoteNote(metadata=note_metadata)


class RemoteNote(object):
    def __init__(self, metadata, everfetch):
        self.metadata = metadata
        self.everfetch = everfetch

    @memoize
    def note(self):
        return self.everfetch.fetch_note(self.metadata.guid)

    @property
    def last_modified(self):
        return self.metadata.last_modified

    def key(self):
        context = get_context()
        assert 'note_key' in context
        note_key = context['note_key']
        notebook_slug = slugify(self.metadata.notebook.name)
        note_slug = slugify(unicode(self.note().title))
        return note_key.format(notebook=notebook_slug, note=note_slug)

    def is_newer_than(self, local_note):
        if self.last_modified > local_note.last_modified:

