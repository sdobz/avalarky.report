#!env/bin/python
from evernote.api.client import EvernoteClient
from evernote.edam.notestore.ttypes import NoteFilter, NotesMetadataResultSpec
from os import path
import shelve

CONTENT_PATH = 'site-gen/content'

# Prod vincent@khougaz.com
# dev_token = "S=s462:U=4e5f584:E=1548920f811:C=14d316fc898:P=1cd:A=en-devtoken:V=2:H=8faad950655d66dfe20808c9c7caa275"
# Dev vincent@khougaz.com
dev_token = "S=s1:U=90cdf:E=1548935fe87:C=14d3184cf68:P=1cd:A=en-devtoken:V=2:H=7369fbadab16c3aee7127e04368ac34f"

client = EvernoteClient(token=dev_token)
noteStore = client.get_note_store()
notebooks = noteStore.listNotebooks()
my_notebook = False
for n in notebooks:
    if n.name == "Blag":
        my_notebook = n

updated_filter = NoteFilter(notebookGuid=my_notebook.guid)
offset = 0
max_notes = 10
result_spec = NotesMetadataResultSpec(includeUpdated=True)
result_list = noteStore.findNotesMetadata(dev_token, updated_filter, offset, max_notes, result_spec)

note_data = shelve.open('evernote.shelve', writeback=True)
new_notes = []
# note is an instance of NoteMetadata
# result_list is an instance of NotesMetadataList

for note in result_list.notes:
    if note.guid not in note_data or note_data[note.guid].updated < note.updated:
        note_data[note.guid] = noteStore.getNote(note.guid, True, True, True, True)
        new_notes.append(note_data[note.guid])

note_data.sync()

import ENML2HTML as enml
import os
import re
import unicodedata
import datetime
from bs4 import BeautifulSoup


class RelativeFileMediaStore(enml.FileMediaStore):
    def __init__(self, note_store, note_guid, path):
        """
        note_store: NoteStore object from EvernoteSDK
        note_guid: Guid of the note in which the resouces exist
        path: The path to store media file
        """
        super(enml.FileMediaStore, self).__init__(note_store, note_guid)
        self.path = path

    def save(self, hash_str, mime_type):
        """
        save the specified hash and return the saved file's URL
        """
        if not os.path.exists(self.path):
            os.makedirs(self.path)
        data = self._get_resource_by_hash(hash_str)
        file_path = os.path.join(self.path, hash_str + enml.MIME_TO_EXTESION_MAPPING[mime_type])
        with open(file_path, "w") as f:
            f.write(data)
        return file_path


def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.
    """
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = unicode(re.sub('[^\w\s-]', '', value).strip().lower())
    return unicode(re.sub('[-\s]+', '-', value))

format_timestamp = lambda ms: datetime.datetime.fromtimestamp(ms/1000).strftime('%Y-%m-%d %H:%M')

for note in new_notes:
    note_slug = slugify(unicode(note.title))

    media_store = RelativeFileMediaStore(noteStore, note.guid,
                                         path=os.path.join(CONTENT_PATH, 'files', note_slug))

    content_soup = BeautifulSoup('<html><head><title>{}</title></head><body></body></html>'.format(note.title))

    def add_meta_tag(name, content):
        new_tag = content_soup.new_tag('meta', content=content)
        new_tag['name'] = name
        content_soup.head.append(new_tag)

    add_meta_tag('slug', note_slug)
    add_meta_tag('category', 'Evernote')
    add_meta_tag('date', format_timestamp(note.created))
    add_meta_tag('modified', format_timestamp(note.updated))

    note_soup = BeautifulSoup(enml.ENMLToHTML(note.content, media_store=media_store, header=False, pretty=False))
    note_soup.div['class'] = 'note'

    content_soup.body.append(note_soup)

    with open(path.join(CONTENT_PATH, note_slug + '.html'), 'w') as f:
        f.write(content_soup.prettify().encode('utf-8'))


from pelican import main
import sys
sys.argv = [
    'test.py',
    'site-gen',
    '--output', 'output',
    '--delete-output-directory',
    '--settings', 'site-gen/pelicanconf.py'
]
sys.exit(main())
