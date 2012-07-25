
__all__ = ('raises', 'returns', 'iterates', 'calls')


class ChainedConsumer(object):
    "Provides a function-like object that returns based on the consumers it contains."
    def __init__(self, consumers):
        self.consumers = consumers
        self._validate(self.consumers)
        self._curr_consumer = None
        self._using_last_consumer = len(consumers) <= 1

    def _validate(self, consumers):
        for consumer in consumers:
            if not callable(getattr(consumer, 'is_at_end', None)):
                raise TypeError('Consumer %r requires is_at_end interface' % consumer)
            if not callable(consumer):
                raise TypeError('Consumer %r must be callable' % consumer)

    def is_at_last_consumer(self):
        return len(self.consumers) <= 1

    def is_repeating_consumer(self):
        return self._using_last_consumer

    def is_at_end(self):
        return (not len(self.consumers) or
                (self.is_last_consumer() and self._curr_consumer.is_at_end()) or
                (self._curr_consumer and
                    self._curr_consumer.is_repeating() and
                    self.has_next_consumer() and
                    self.consumers[0].is_at_end()))

    def is_repeating(self):
        return not len(self.consumers) or (
                self.is_last_consumer() and self._curr_consumer.is_repeating())

    def process_consumer(self, args, kwargs, consumer):
        return consumer(*args, **kwargs)

    def has_next_consumer(self):
        return len(self.consumers) > 0

    def next_consumer(self):
        self._using_last_consumer = self.is_at_last_consumer()
        if self.is_at_last_consumer():
            return self.consumers[-1]
        return self.consumers.pop(0)

    def is_last_consumer(self):
        return self._curr_consumer == self.consumers[-1]

    def _can_consume_next(self):
        return self._curr_consumer.is_repeating() and not self.is_last_consumer()

    def __call__(self, *args, **kwargs):
        if not self._curr_consumer or self._can_consume_next():
            self._curr_consumer = self.next_consumer()
        return self.process_consumer(args, kwargs, self._curr_consumer)


class ValueConsumer(object):
    """Provides a function-like object that returns a series of values provided."""
    def __init__(self, values):
        self.values = list(values)
        self._validate(self.values)
        self._has_consumed_last_value = len(self.values) == 0

    def is_at_end(self):
        return len(self.values) <= 1

    def is_repeating(self):
        return self._has_consumed_last_value

    def _validate(self, values):
        pass

    def process_value(self, args, kwargs, value):
        return value

    def next_value(self):
        self._has_consumed_last_value = self.is_at_end()
        return self.values[-1] if self.is_at_end() else self.values.pop(0)

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

def calls(*functions, **kwargs):
    """Returns a callable that returns the value from the invocation of each function.
    Unless passthrough=True, all functions are assumed to accept no arguments.
    """
    passthrough = kwargs.get('passthough', None)
    if not passthrough:
        functions = [lambda *a, **k: fn() for fn in functions]
    return FunctionConsumer(functions)

def returns(*values):
    """Returns a callable that return the provided values in sequencially,
    repeating the last value indefinitely.
    """
    return ValueConsumer(values)


def iterates(*elements):
    """Returns an iterable (generator) of contains all the elements.
    """
    return IteratorConsumer(elements)
