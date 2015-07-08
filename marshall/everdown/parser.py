import ENML2HTML as enml
from bs4 import BeautifulSoup
from os import path
import os
from .util import slugify
import datetime


class EverdownStore(enml.MediaStore):
    files_dir = 'files'

    def __init__(self, note_store, note_guid, note_root):
        super(EverdownStore, self).__init__(note_store, note_guid)
        self.file_root = path.join(note_root, self.files_dir)

    def save(self, hash_str, mime_type):
        """
        save the specified hash and return the saved file's URL
        """
        if not path.exists(self.file_root):
            os.makedirs(self.file_root)
        data = self._get_resource_by_hash(hash_str)
        filename = hash_str + enml.MIME_TO_EXTESION_MAPPING[mime_type]

        # Files are written relative to content_root
        with open(path.join(self.file_root, filename), "w") as f:
            f.write(data)

        # The resource path is returned into img tags
        return path.join(self.files_dir, filename)


format_timestamp = lambda ms: datetime.datetime.fromtimestamp(ms/1000).strftime('%Y-%m-%d %H:%M')


def save_note(note, note_store, output, notebook):
    notebook_slug = slugify(notebook.name)
    note_slug = slugify(unicode(note.title))
    note_root = path.join(output, notebook_slug, note_slug)
    media_store = EverdownStore(note_store, note.guid, note_root=note_root)

    content_soup = BeautifulSoup('<html><head><title>{}</title></head><body></body></html>'.format(note.title))

    def add_meta_tag(name, content):
        new_tag = content_soup.new_tag('meta', content=content)
        new_tag['name'] = name
        content_soup.head.append(new_tag)

    add_meta_tag('slug', note_slug)
    add_meta_tag('category', notebook.name)
    add_meta_tag('date', format_timestamp(note.created))
    add_meta_tag('modified', format_timestamp(note.updated))

    note_soup = BeautifulSoup(enml.ENMLToHTML(note.content, media_store=media_store, header=False, pretty=False))
    note_soup.div['class'] = 'note'

    content_soup.body.append(note_soup)

    with open(path.join(note_root, 'index.html'), 'w') as f:
        f.write(content_soup.prettify().encode('utf-8'))
