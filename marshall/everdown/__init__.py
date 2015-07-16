from evernote.api.client import EvernoteClient
from evernote.edam.notestore.ttypes import NoteFilter, NotesMetadataResultSpec
import fnmatch
import re
import pickle
from os import path
from .util import slugify
from .parser import save_note
import logging
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
log = logging.getLogger(__name__)


def run(settings):
    log.info('Starting run')

    token = settings['token']
    cache_file = settings['cache']
    content_path = settings['content path']
    file_path = settings['file path']
    html_path = settings['html path']

    notebook_filters = [
        re.compile(fnmatch.translate(filter_glob)) for filter_glob in settings['notebooks']
    ]

    client = EvernoteClient(token=token)
    note_store = client.get_note_store()
    notebooks = get_notebooks(note_store)

    for notebook in filter_notebooks(notebooks, notebook_filters):
        log.info('Checking {}'.format(notebook.name))
        unchanged_notes = 0

        for note_metadata in get_note_metadata(notebook, note_store, token).notes:
            if path.exists(cache_file):
                with open(cache_file) as fh:
                    cache = pickle.load(fh)
            else:
                cache = {}
            unchanged_notes += save_if_stale(cache, note_metadata, note_store, content_path, notebook, html_path, file_path)
            with open(cache_file, 'wb') as fh:
                pickle.dump(cache, fh)

        log.info('Skipped {} unchanged notes'.format(unchanged_notes))


def save_if_stale(cache, new_note, note_store, content_path, notebook, html_path, file_path):
    unchanged_notes = 0
    note_guid = new_note.guid

    old_note = cache[note_guid] if note_guid in cache else None

    if old_note is None or old_note.updated < new_note.updated:
        log.info('Retrieving stale or missing note {}'.format(note_guid))
        new_note = note_store.getNote(note_guid, True, True, True, True)
        cache[note_guid] = new_note
        log.info('Saving fresh note: {}'.format(new_note.title))

        save_note(new_note, note_store, content_path, notebook, html_path, file_path)
        log.info('Wrote note')
    else:
        unchanged_notes += 1
    return unchanged_notes


def get_notebooks(note_store):
    return note_store.listNotebooks()


def filter_notebooks(notebooks, notebook_filters):
    passed_notebooks = []

    for notebook in notebooks:
        for filter in notebook_filters:
            if filter.match(notebook.name):
                passed_notebooks.append(notebook)
                continue

    return passed_notebooks


def get_note_metadata(notebook, note_store, token):
    updated_filter = NoteFilter(notebookGuid=notebook.guid)
    offset = 0
    max_notes = 10
    result_spec = NotesMetadataResultSpec(includeUpdated=True)
    return note_store.findNotesMetadata(token, updated_filter, offset, max_notes, result_spec)


