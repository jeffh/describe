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
        @wraps(func)
        def decorated(*args, **kwargs):
            with self as obj:
                return func(obj, *args, **kwargs)
        return decorated

