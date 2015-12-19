def update_notes(everfetch, existing, remote):
    updated_notes = remote - existing


class Note(object):
    metadata = None

    def __init__(self, data):
        if 'metadata' in data:
            self.metadata = data['metadata']