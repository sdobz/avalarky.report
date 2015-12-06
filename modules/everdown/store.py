import pickle
from os import path, makedirs


def make_store(settings):
    """
    :rtype: Store
    """
    # I am gross, but this is fun code (aka bad)
    assert 'type' in settings
    assert settings['type'] in store_classes
    return store_classes[settings['type']](settings)


class Store(object):
    """
    All stores conform to this interface
    """
    def __init__(self, settings):
        pass

    def save(self, key, data):
        pass

    def load(self, key):
        pass


class PickleStore(Store):
    """
    Not thread safe, etc.
    """
    store = None
    filename = None

    def __init__(self, settings):
        assert 'filename' in settings
        self.filename = settings['filename']

        if path.exists(self.filename):
            with open(self.filename, 'r') as f:
                self.store = pickle.load(f)
        else:
            self.store = {}

        super(PickleStore, self).__init__(settings)

    def save(self, key, data):
        self.store[key] = data
        with open(self.filename, 'wb') as f:
            pickle.dump(self.store, f, protocol=pickle.HIGHEST_PROTOCOL)

    def load(self, key):
        if key in self.store:
            return self.store[key]


class FileStore(Store):
    root = None

    def __init__(self, settings):
        assert 'root' in settings
        self.root = settings['root']
        super(FileStore, self).__init__(settings)

    def save(self, key, data):
        key_path = path.join(self.root, key)
        base_dir = path.dirname(key_path)
        if not path.exists(base_dir):
            makedirs(base_dir, 0755)

        with open(key_path, 'wb') as f:
            f.write(data)

    def load(self, key):
        key_path = path.join(self.root, key)
        if path.exists(key_path):
            with open(key_path, 'r') as f:
                return f.read()

store_classes = {
    'pickle': PickleStore,
    'file': FileStore
}
