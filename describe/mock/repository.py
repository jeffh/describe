
default = None

class Repository(object):
    """Represents a collection of instanciated mock objects.
    """
    def __init__(self):
        self.mocks = []

    def __repr__(self):
        return "<Repository:%r>" % self.mocks

    def __iter__(self):
        return iter(self.mocks)

    def __contains__(self, obj):
        return obj in self.mocks

    def register(self, mock):
        self.mocks.append(mock)
        return mock

    def clear(self):
        self.mocks = []

    def verify(self, strict=True):
        try:
            for m in self.mocks:
                m.verify(strict)
        except:
            self.clear()
            raise
        return self

default = Repository()
