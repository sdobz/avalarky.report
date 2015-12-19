import pytest
from . import hashabledict, make_store, store_cache, store_classes, Store, StoreMisconfig

@pytest.fixture
def clear_cache(request):
    """
    When injected this fixture clears store_cache
    """
    def clear():
        store_cache.clear()
    request.addfinalizer(clear)


def test_hashabledict():
    """ A hashabledict should have the same hash for the same dict """
    a = hashabledict({'a': 1})
    b = hashabledict({'a': 2})
    c = hashabledict({'a': 1})

    assert hash(a) != hash(b)
    assert hash(a) == hash(c)

    a = hashabledict({'a': 1, 'b': 2})
    b = hashabledict({'b': 2, 'a': 1})
    assert hash(a) == hash(b)


def test_hashabledict_as_key():
    """ A hashabledict should be able to be used as a dictionary key """
    # Same data, different order
    a = hashabledict({'a': 1, 'b': 2})
    b = hashabledict({'b': 2, 'a': 1})

    d = dict()
    d[a] = True
    d[b] = False
    # Changing b changes a
    assert d[a] == False

    # Different data
    c = hashabledict({'a': 3, 'b': 4})
    d = hashabledict({'a': 2, 'b': 1})

    # Changing d does not change c
    d[c] = True
    d[d] = False
    assert d[c] == True


class TestStore(Store):
    """
    Minimal store with descriptive getitem and keys
    """
    def __getitem__(self, key):
        """ Appends -value to key when indexed (store['key'] == 'key-value') """
        return '{}-value'.format(key)

    def keys(self):
        return 'a', 'b', 'c'

store_classes['test'] = TestStore
test_store_desc = {
    'type': 'test'
}
test_store_desc_hash = hashabledict(test_store_desc)


def test_Store_defaults(clear_cache):
    """ Store instances should provide default iteritems and iteration """
    store = make_store(test_store_desc)

    # Testing the TestStore...
    assert store.keys() == ('a', 'b', 'c')
    assert store['key'] == 'key-value'

    # Iteritems should iterate over all key value pairs
    assert tuple(store.iteritems()) == (('a', 'a-value'), ('b', 'b-value'), ('c', 'c-value'))

    # Iteration should iterate over values
    assert tuple(store) == ('a-value', 'b-value', 'c-value')


def test_make_store_fails_without_type(clear_cache):
    """ When make_store is called without a type it should raise a descriptive error """
    with pytest.raises(StoreMisconfig):
        # No 'type' key given is a misconfiguration
        make_store({})


def test_make_store_fails_with_bad_type(clear_cache):
    """ When called with a bad type it should raise a descriptive error"""
    assert 'bad_type' not in store_classes
    with pytest.raises(StoreMisconfig):
        make_store({'type': 'bad_type'})


def test_make_store_cache(clear_cache):
    """
    make_store should cache the store for each description, so if the same description is used it will
    return the same store instance.
    """
    # Should not start cached
    assert test_store_desc_hash not in store_cache
    # Making a store caches it by store_desc
    store = make_store(test_store_desc)
    # As this key
    assert test_store_desc_hash in store_cache

    # make_store should return the same cached object with the same desc
    store_id = id(store)
    # You can check by testing the id
    assert id(make_store(test_store_desc)) == store_id
    del store_cache[test_store_desc_hash]
    # If it is not cached then it returns a new instance
    assert id(make_store(test_store_desc)) != store_id

    # Different descriptions (such as with a name) produce different instances
    test_store_desc['name'] = 'a'
    store_a = make_store(test_store_desc)

    test_store_desc['name'] = 'b'
    store_b = make_store(test_store_desc)
    assert id(store_a) != id(store_b)
    del test_store_desc['name']


def test_make_store_class(clear_cache):
    """ make_store should return the proper class per type """
    assert isinstance(make_store(test_store_desc), TestStore)
