import collections

class FrozenDict(collections.Mapping):
    """Based on the stackoverflow question for FrozenDict."""

    def __init__(self, *args, **kwargs):
        self._d = dict(*args, **kwargs)
        self._hash = None

    def __repr__(self):
        return repr(self._d)

    def __iter__(self):
        return iter(self._d)

    def __len__(self):
        return len(self._d)

    def __getitem__(self, key):
        return self._d[key]

    def __contains__(self, key):
        return key in self._d

    def __setitem__(self, key, value):
        raise TypeError, '%(class)r does not support item assignment.' % {
            'class': self.__class__.__name__
        }

    def __str__(self):
        return str(self._d)

    def __eq__(self, other):
        return self._d == other

    def has_key(self, key):
        return self._d.has_key(key)

    def keys(self):
        return self._d.keys()

    def values(self):
        return self._d.values()

    def items(self):
        return self._d.items()

    def iteritems(self):
        return self._d.iteritems()

    def iterkeys(self):
        return self._d.iterkeys()

    def viewitems(self):
        return self._d.viewitems()

    def viewkeys(self):
        return self._d.viewkeys()

    def __hash__(self):
        if self._hash is None:
            self._hash = 0
            for key, value in self.iteritems():
                self._hash ^= hash(key)
                self._hash ^= hash(value)
        return self._hash
