import sys
from types import ModuleType
from functools import wraps

from describe.spec.utils import Replace, with_metadata
from describe.mock.stub import stub

__all__ = ['patch']

# formatter will pick this up as remove traceback that has this in globals
# it is in this module because this is one of the  closest to the invocation
# of the actual specs.
__DESCRIBE_FRAME_MARK = True


class DictReplacement(object):
    def __init__(self, curr, new):
        self.curr, self.new = curr, new
        self.old = dict(self.curr)

    def _cleardict(self):
        for key in dict(self.curr).keys():
            del self.curr[key]

    def _copyfrom(self, dictionary):
        for key in dictionary:
            self.curr[key] = dictionary[key]

    def start(self):
        self.old = dict(self.curr)
        self._cleardict()
        self._copyfrom(self.new)
        return self

    def stop(self):
        self._cleardict()
        self._copyfrom(self.old)
        return self

    def __enter__(self):
        self.start()
        return self.curr

    def __exit__(self, type, error, traceback):
        self.stop()

    def __call__(self, func):
        def decorator(fn):
            @wraps(fn)
            def decorated(*args, **kwargs):
                with self:
                    return fn(*args, **kwargs)
            return decorated

        return with_metadata(decorator)(func)


class Patcher(object):
    def __init__(self):
        self.getattr, self.setattr = getattr, setattr

    def object(self, obj, attr, value=None):
        return Replace(obj, attr, value or stub())

    def __call__(self, objectpath, value=None):
        modulepath, obj = objectpath.rsplit('.', 1)
        mod = __import__(modulepath)
        if not hasattr(mod, obj):
            raise ImportError("%r does not have %r" % (mod, obj))
        return self.object(mod, obj, value)

    def dict(self, current, new):
        return DictReplacement(current, new)

patch = Patcher()



