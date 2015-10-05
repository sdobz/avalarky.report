# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup, NavigableString
from os import path
from StringIO import StringIO
import os
import re
from .util import slugify, ensure_dir, protect_rate_limit
from .image import scale_and_crop, constrain_size
import datetime
from pelican.urlwrappers import Tag
from PIL import Image
from logging import getLogger
log = getLogger(__name__)


format_timestamp = lambda ms: datetime.datetime.fromtimestamp(ms/1000).strftime('%Y-%m-%d %H:%M')


MIME_TO_EXTESION_MAPPING = {
    'image/png': '.png',
    'image/jpg': '.jpg',
    'image/jpeg': '.jpg',
    'image/gif': '.gif'
}


def save_note(media_cache, note, note_info, note_paths, pelican_settings):
    notebook_slug = slugify(note_info.notebook.name)
    note_slug = slugify(unicode(note.title))

    soup = BeautifulSoup('<html><head><title>{}</title></head><body></body></html>'.format(note.title), 'html.parser')
    note_soup = BeautifulSoup(note.content, 'html.parser').find('en-note')
    note_soup.name = 'div'
    note_soup['class'] = 'note'
    soup.body.append(note_soup)

    meta_tags = {}

    def add_meta_tag(name, content):
        meta_tags[name] = content
        new_tag = soup.new_tag('meta', content=content)
        new_tag['name'] = name
        soup.head.append(new_tag)

    add_meta_tag('slug', note_slug)
    add_meta_tag('category', note_info.notebook.name)
    add_meta_tag('date', format_timestamp(note.created))
    add_meta_tag('modified', format_timestamp(note.updated))

    path_map = {
        'notebook': notebook_slug,
        'note': note_slug
    }
    content_path = note_paths.content.format(**path_map)
    html_path = note_paths.html.format(**path_map)
    file_path = note_paths.file.format(**path_map)

    replace_media_tags(media_cache, soup, note, note_info.store, html_path, file_path, add_meta_tag)

    if note.attributes.latitude is not None and note.attributes.longitude is not None:
        place = note_info.get_place(note.attributes.latitude, note.attributes.longitude)
        if place:
            add_meta_tag('city', place)
        else:
            add_meta_tag('latitude', note.attributes.latitude)
            add_meta_tag('longitude', note.attributes.longitude)

    tags = linkify_soup(soup, soup.new_tag, pelican_settings)
    add_meta_tag('tags', u', '.join(tags))

    summary = get_summary(note_soup, 120)
    add_meta_tag('summary', summary)

    # Facebook OG tags
    add_meta_tag('og:title', note.title)
    add_meta_tag('og:site_name', 'avalarky report')
    add_meta_tag('og:description', summary)
    add_meta_tag('og:type', 'article')
    if 'hero_image' in meta_tags:
        add_meta_tag('og:image', meta_tags['hero_image'])

    if not path.exists(content_path):
        os.makedirs(content_path, mode=0755)

    with open(path.join(content_path, 'index.html'), 'w') as f:
        f.write(soup.prettify().encode('utf-8'))


def get_summary(soup, summary_length):
    word_list = soup.get_text(separator=u' ').strip().replace(u'\n', u'—').split()
    summary = ''
    while len(summary) < summary_length and len(word_list) > 0:
        summary += ' ' + word_list.pop(0)
    return summary.strip()


def replace_media_tags(media_cache, soup, note, note_store, html_path, file_path, add_meta_tag):
    all_media = soup.find_all('en-media')
    if not len(all_media) > 0 and not path.exists(file_path):
        os.makedirs(file_path, mode=0755)

    # TODO: pending settings refactor
    scaled_size = (400, 400)
    hero_size = (800, 300)
    thumbnail_size = (200, 200)

    for i, media in enumerate(all_media):
        resource_hash = media['hash']
        ext = MIME_TO_EXTESION_MAPPING[media['type']]

        full_filename = '{}{}'.format(resource_hash, ext)
        scaled_filename = '{}-{}x{}{}'.format(resource_hash, scaled_size[0], scaled_size[1], ext)
        outputs = [
            (path.join(file_path, full_filename), None, None),
            (path.join(file_path, scaled_filename), scaled_size, constrain_size),
        ]
        if i == 0:
            thumbnail_filename = 'thumbnail{}'.format(ext)
            hero_filename = 'hero{}'.format(ext)
            outputs += [
                (path.join(file_path, thumbnail_filename), thumbnail_size, scale_and_crop),
                (path.join(file_path, hero_filename), hero_size, scale_and_crop)
            ]

            add_meta_tag('hero_image', path.join(html_path, hero_filename))
            add_meta_tag('thumbnail_image', path.join(html_path, thumbnail_filename))

        save_media(media_cache, resource_hash, note_store, note.guid, outputs)

        anchor = soup.new_tag('a', href=path.join(html_path, full_filename), target='_blank')
        img = soup.new_tag('img', src=path.join(html_path, scaled_filename))
        anchor.append(img)

        media.replace_with(anchor)


def save_media(media_cache, resource_hash, note_store, note_guid, outputs):
    new_outputs = [output for output in outputs if not path.exists(output[0])]

    if len(new_outputs) == 0:
        return

    log.info('Resource {} has new outputs'.format(resource_hash))

    data = media_cache.load(resource_hash)
    if not data:
        data = get_resource_by_hash(note_store, note_guid, resource_hash)
        log.info('Retrieved resource')
        media_cache.save(resource_hash, data)

    im = Image.open(StringIO(data))

    for filename, size, resize_method in outputs:
        if size is not None and resize_method is not None:
            im_o = resize_method(im, size)
        else:
            im_o = im

        ensure_dir(filename)
        im_o.save(filename, quality=90)


def get_resource_by_hash(note_store, note_guid, resource_guid):
    """
    get resource by its hash
    """
    resource_guid_bin = resource_guid.decode('hex')
    resource = protect_rate_limit(note_store.getResourceByHash, note_guid, resource_guid_bin, True, False, False)
    return resource.data.body

tag_re = re.compile('(#\w+)')


def linkify_soup(soup, new_tag, pelican_settings):
    assert hasattr(soup, 'contents')
    tags = set()
    old_elements = [e for e in soup.contents]
    for element in old_elements:
        if not isinstance(element, NavigableString):
            tags = tags.union(linkify_soup(element, new_tag, pelican_settings))
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
                    tag = Tag(segment, pelican_settings)
                    # This is how pelican does tag urls...
                    new_e = new_tag("a", href=pelican_settings['SITEURL'] + '/' + tag.url)
                    new_e.string = segment
                    tags.add(segment[1:])
                insertion_target.insert_after(new_e)
                insertion_target = new_e

        element.extract()

    return tags
