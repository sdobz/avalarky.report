from evernote.api.client import EvernoteClient
from evernote.edam.notestore.ttypes import NoteFilter, NotesMetadataResultSpec
from collections import namedtuple
import fnmatch
import re
from .util import slugify, protect_rate_limit
from .parser import save_note
from .geolocate import create_get_place
from .store import make_store
import logging
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)
log = logging.getLogger(__name__)

NoteInfo = namedtuple('NoteInfo', 'metadata notebook store token get_place')
NotePaths = namedtuple('NotePaths', 'content html file')


def run(settings, pelican_settings):
    log.info('Starting run')

    if settings['sandbox']:
        token = settings['token-sandbox']
        sandbox = True
    else:
        token = settings['token']
        sandbox = False

    note_cache = make_store(settings['note cache'])
    media_cache = make_store(settings['media cache'])
    note_paths = NotePaths(
        content=settings['content path'],
        file=settings['file path'],
        html=settings['html path']
    )
    get_place = create_get_place(settings['location'])

    notebook_filters = [
        re.compile(fnmatch.translate(filter_glob)) for filter_glob in settings['notebooks']
    ]

    client = EvernoteClient(token=token, sandbox=sandbox)
    note_store = protect_rate_limit(client.get_note_store)
    notebooks = get_notebooks(note_store)

    for notebook in filter_notebooks(notebooks, notebook_filters):
        log.info('Checking {}'.format(notebook.name))
        unchanged_notes = 0

        for note_info in get_note_info(notebook, note_store, token, get_place):
            unchanged_notes += save_if_stale(note_cache, media_cache, note_info, note_paths, settings, pelican_settings)

        if unchanged_notes > 0:
            log.info('Skipped {} unchanged notes'.format(unchanged_notes))


def save_if_stale(note_cache, media_cache, note_info, note_paths, settings, pelican_settings):
    unchanged_notes = 0
    note_guid = note_info.metadata.guid

    note = note_cache.load(note_guid)
    new_note = None

    if note is None or note.updated < note_info.metadata.updated:
        log.info('Retrieving stale or missing note {}'.format(note_guid))
        note = protect_rate_limit(note_info.store.getNote, note_guid, True, False, False, False)
        note_cache.save(note_guid, note)
        new_note = True
        log.info('Fetched'.format(note.title))

    if settings['rebuild notes'] or new_note:
        try:
            save_note(media_cache, note, note_info, note_paths, pelican_settings)
        except BaseException as e:
            log.error('Caught exception: {}'.format(e))
        log.info('Wrote note: {}'.format(note.title))
    else:
        unchanged_notes += 1
    return unchanged_notes


def get_notebooks(note_store):
    return protect_rate_limit(note_store.listNotebooks)


def filter_notebooks(notebooks, notebook_filters):
    passed_notebooks = []

    for notebook in notebooks:
        for filter in notebook_filters:
            if filter.match(notebook.name):
                passed_notebooks.append(notebook)
                continue

    return passed_notebooks


def get_note_info(notebook, note_store, token, get_place):
    updated_filter = NoteFilter(notebookGuid=notebook.guid)
    offset = 0
    max_notes = 10
    result_spec = NotesMetadataResultSpec(includeUpdated=True)
    while True:
        note_results = protect_rate_limit(note_store.findNotesMetadata, token, updated_filter, offset, max_notes, result_spec)
        for metadata in note_results.notes:
            yield NoteInfo(
                metadata=metadata,
                notebook=notebook,
                store=note_store,
                token=token,
                get_place=get_place
            )
        offset += max_notes

        if offset > note_results.totalNotes:
            break
