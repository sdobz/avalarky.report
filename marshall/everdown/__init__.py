from evernote.api.client import EvernoteClient
from evernote.edam.notestore.ttypes import NoteFilter, NotesMetadataResultSpec
import fnmatch
import re
from .util import slugify
from .parser import save_note


def run(settings):
    token = settings['token']
    output = settings['output']
    notebook_filters = [
        re.compile(fnmatch.translate(filter_glob)) for filter_glob in settings['notebooks']
    ]

    client = EvernoteClient(token=token)
    note_store = client.get_note_store()
    notebooks = get_notebooks(note_store)

    for notebook in filter_notebooks(notebooks, notebook_filters):
        for note_metadata in get_note_metadata(notebook, note_store, token).notes:
            save_note(note_store.getNote(note_metadata.guid, True, True, True, True), note_store, output, notebook)


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


