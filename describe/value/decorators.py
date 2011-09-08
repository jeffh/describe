
class VerifyDecorator(object):
    def __init__(self, value):
        self.value = value
    
    def __call__(self, func):
        func(self.value)

class DeferredDecorator(object):
    """Stores a function and its arguments to use."""
    def __init__(self, func, args=(), kwargs=None):
        if kwargs is None:
            kwargs = {}
        self.args = args
        self.kwargs = kwargs
        self.func = func
        self.__name__ = getattr(func, '__name__', repr(func))

    def __call__(self):
        return self.func(*self.args, **self.kwargs)

