class LocalNote(object):
    dirty = False

    def __init__(self, data, media_store):
        self.data = data
        self.media_store = media_store

    @property
    def last_modified(self):
        # TODO: Test assumption
        return self.data['metadata']['last_modified']

    def update_from(self, remote_note):
        self.data['content'] = remote_note.content()
        self.data['metadata'] = remote_note.metadata
        pass

    def update_media(self, remote_note):
        # Get local media
        # Check remote media hashes
        # Download nonexisting, remove from local
        # Delete remaining local
        pass
