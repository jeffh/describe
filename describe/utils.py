from functools import wraps, partial


class Replace(object):
    def __init__(self, obj, name, value, **kwargs):
        self.obj, self.name, self.value = obj, name, value
        self.noop = kwargs.get('noop', False)

    def set_noop(self, value):
        self.noop = bool(value)
        return self

    def start(self):
        if self.noop: return self
        self.original = getattr(self.obj, self.name)
        setattr(self.obj, self.name, self.value)
        return self
    replace = start

    def stop(self):
        if self.noop: return self
        setattr(self.obj, self.name, self.original)
        return self
    restore = stop

    def __enter__(self):
        self.start()
        return self.value

    def __exit__(self, type, info, exception):
        self.stop()

    def __call__(self, func):
        def decorator(fn):
            @wraps(fn)
            def decorated(*args, **kwargs):
                with self as obj:
                    return fn(obj, *args, **kwargs)
            return decorated
        return with_metadata(decorator)(func)


def with_metadata(decorator):
    """Creates a new decorator that records the function metadata on the generated
    decorated function.
    """
    @wraps(decorator)
    def new_decorator(func):
        decorated = decorator(func)
        # if the decorator is a "no-op", do nothing
        if not callable(decorator):
            return decorated
        # record data
        decorated.__decorator__ = decorator

        if isinstance(func, partial):
            # partials are objects that store the true function somewhere else
            decorated.__wraps__ = func.keywords['wrapped']
        else:
            decorated.__wraps__ = func
        return decorated

    return new_decorator

