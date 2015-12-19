import pickle
from os import path, makedirs
import os
import toml


class hashabledict(dict):
    def __key(self):
        return tuple((k,self[k]) for k in sorted(self))

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return self.__key() == other.__key()

store_cache = {}


class StoreMisconfig(Exception):
    pass


def make_store(store_desc):
    """
    :rtype: Store
    """
    if 'type' not in store_desc:
        raise StoreMisconfig("'type' is a required parameter in store descriptions")

    if store_desc['type'] not in store_classes:
        raise StoreMisconfig("type: '{}' not valid".format(store_desc['type']))

    global store_cache
    store_desc_key = hashabledict(store_desc)

    if store_desc_key in store_cache:
        return store_cache[store_desc_key]

    # I am gross, but this is fun code (aka bad)

    store = store_classes[store_desc['type']](store_desc)
    store_cache[store_desc_key] = store
    return store


class Store(object):
    """
    All stores conform to this interface
    """
    def __init__(self, settings):
        pass

    def __getitem__(self, key):
        raise NotImplemented

    def __setitem__(self, key, value):
        raise NotImplemented

    def keys(self):
        raise NotImplemented

    def iteritems(self):
        for key in self.keys():
            yield key, self[key]

    def __iter__(self):
        for key in self.keys():
            yield self[key]


class MemoryStore(Store, dict):
    def __init__(self, settings):
        assert 'name' in settings
        super(MemoryStore, self).__init__(settings)


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

        self.keys = self.store.keys

        super(PickleStore, self).__init__(settings)

    def __setitem__(self, key, data):
        self.store[key] = data
        with open(self.filename, 'wb') as f:
            pickle.dump(self.store, f, protocol=pickle.HIGHEST_PROTOCOL)

    def __getitem__(self, key):
        return self.store[key]


class FileStore(Store):
    root = None

    def __init__(self, settings):
        assert 'root' in settings
        self.root = settings['root']
        super(FileStore, self).__init__(settings)

    def __setitem__(self, key, data):
        key_path = path.join(self.root, key)
        base_dir = path.dirname(key_path)
        if not path.exists(base_dir):
            makedirs(base_dir, 0755)

        with open(key_path, 'wb') as f:
            f.write(data)

    def __getitem__(self, key):
        key_path = path.join(self.root, key)
        if path.exists(key_path):
            with open(key_path, 'r') as f:
                return f.read()
        else:
            raise KeyError

    def keys(self):
        for subdir, dirs, files in os.walk(self.root):
            for file in files:
                yield os.sep.join((subdir, file))


class KyreStore(FileStore):
    def __setitem__(self, key, data):
        super(KyreStore, self).__setitem__(key, toml.dumps(data))

    def __getitem__(self, key):
        return toml.loads(super(KyreStore, self).__getitem__(key))


store_classes = {
    'memory': MemoryStore,
    'pickle': PickleStore,
    'file': FileStore,
    'kyre': KyreStore,
}