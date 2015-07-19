import ENML2HTML as enml
from bs4 import BeautifulSoup, NavigableString
from os import path
import os
import re
from .util import slugify
import datetime


class EverdownStore(enml.MediaStore):
    def __init__(self, note_store, note_guid, html_path, file_path):
        super(EverdownStore, self).__init__(note_store, note_guid)
        self.html_path = html_path
        self.file_path = file_path

    def save(self, hash_str, mime_type):
        """
        save the specified hash and return the saved file's URL
        """
        data = self._get_resource_by_hash(hash_str)
        filename = hash_str + enml.MIME_TO_EXTESION_MAPPING[mime_type]

        if not path.exists(self.file_path):
            os.makedirs(self.file_path)

        # Files are written relative to content_root
        with open(path.join(self.file_path, filename), "w") as f:
            f.write(data)

        # The resource path is returned into img tags
        return path.join(self.html_path, filename)


format_timestamp = lambda ms: datetime.datetime.fromtimestamp(ms/1000).strftime('%Y-%m-%d %H:%M')


def save_note(note, note_info, note_paths):
    notebook_slug = slugify(note_info.notebook.name)
    note_slug = slugify(unicode(note.title))
    # TODO: Bad code, magical variable reformatting
    path_map = {
        'notebook': notebook_slug,
        'note': note_slug
    }
    content_path = note_paths.content.format(**path_map)
    media_store = EverdownStore(note_info.store, note.guid, note_paths.html.format(**path_map), note_paths.file.format(**path_map))

    content_soup = BeautifulSoup('<html><head><title>{}</title></head><body></body></html>'.format(note.title), features='html.parser')

    def add_meta_tag(name, content):
        new_tag = content_soup.new_tag('meta', content=content)
        new_tag['name'] = name
        content_soup.head.append(new_tag)

    add_meta_tag('slug', note_slug)
    add_meta_tag('category', note_info.notebook.name)
    add_meta_tag('date', format_timestamp(note.created))
    add_meta_tag('modified', format_timestamp(note.updated))

    if note.attributes.latitude is not None and note.attributes.longitude is not None:
        add_meta_tag('city', note_info.get_city(note.attributes.latitude, note.attributes.longitude))

    note_soup = BeautifulSoup(enml.ENMLToHTML(note.content, media_store=media_store, header=False, pretty=False), 'html.parser')
    note_soup.div['class'] = 'note'

    tags = linkify_soup(note_soup, note_soup.new_tag)
    add_meta_tag('tags', u', '.join(tags))

    first_img = note_soup.find('img')
    if first_img:
        add_meta_tag('promoted-image', first_img.attrs['src'])

    content_soup.body.append(note_soup)

    if not path.exists(content_path):
        os.makedirs(content_path)

    with open(path.join(content_path, 'index.html'), 'w') as f:
        f.write(content_soup.prettify().encode('utf-8'))


tag_re = re.compile('(#\w+)')


def linkify_soup(soup, new_tag):
    assert hasattr(soup, 'contents')
    tags = set()
    old_elements = [e for e in soup.contents]
    for element in old_elements:
        if not isinstance(element, NavigableString):
            tags = tags.union(linkify_soup(element, new_tag))
            continue

        segments = tag_re.split(element)

        if len(segments) <= 1:
            continue

        insertion_target = element

        for segment in segments:
            if len(segment) > 0:
                if tag_re.match(segment) is None:
                    new_e = NavigableString(segment)
                else:
                    new_e = new_tag("a", href="#")
                    new_e.string = segment
                    tags.add(segment[1:])
                insertion_target.insert_after(new_e)
                insertion_target = new_e

        element.extract()

    return tags
