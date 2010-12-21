
class VerifyDecorator(object):
    def __init__(self, value):
        self.value = value
    
    def __call__(self, func):
        func(self.value)

class DeferredDecorator(object):
    def __init__(self, func, args=(), kwargs=None):
        if kwargs is None:
            kwargs = {}
        self.args = args
        self.kwargs = kwargs
        self.func = func
        self.__name__ = func.__name__
    
    def __call__(self):
        return self.func(*self.args, **self.kwargs)
        