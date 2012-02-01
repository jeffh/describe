
def createfn(name, doc=None):
    fn = lambda:0
    fn.__name__ = name
    fn.__doc__ = doc
    return fn

class SampleError(AssertionError):
    def __eq__(self, other):
        return self.message == other.message

