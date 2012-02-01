
__all__ = ('raises', 'returns', 'iterates')


class ValueConsumer(object):
    """Provides a function-like object that returns a series of values provided."""
    def __init__(self, values):
        self.values = list(values)
        self._validate(self.values)

    def _validate(self, values):
        pass

    def process_value(self, args, kwargs, value):
        return value

    def next_value(self):
        return self.values.pop(0) if len(self.values) > 1 else self.values[-1]

    def __call__(self, *args, **kwargs):
        return self.process_value(args, kwargs, self.next_value())


class ErrorConsumer(ValueConsumer):
    """Provides a function-like object that raises a series of exceptions provided."""
    def process_value(self, args, kwargs, value):
        raise value

    def _validate(self, values):
        for exc in values:
            if not (isinstance(exc, Exception) or issubclass(exc, Exception)):
                raise TypeError('%r is not an instance or class of Exception' % exc)


class FunctionConsumer(ValueConsumer):
    """Provides a function-like object that returns the value of calling a series
    of functions provided.
    """
    def process_value(self, args, kwargs, value):
        return value(*args, **kwargs)


class IteratorConsumer(ValueConsumer):
    """Provides a function-like object that returns an iterator (a generator) of calling
    a series of functions provided.
    """
    def __call__(self, *args, **kwargs):
        total = len(self.values)
        for i in range(total):
            yield self.process_value(args, kwargs, self.next_value())

# Public API

def raises(*errors):
    """Returns a callable that raises the provided errors in order. Repeating the last
    error indefinitely.
    """
    return ErrorConsumer(errors)


def returns(*values):
    """Returns a callable that return the provided values in sequencially,
    repeating the last value indefinitely.
    """
    return ValueConsumer(values)


def iterates(*elements):
    """Returns an iterable (generator) of contains all the elements.
    """
    return IteratorConsumer(elements)
