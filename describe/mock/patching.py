import sys
from types import ModuleType
from functools import wraps

from describe.spec.utils import Replace, with_metadata
from describe.mock.stubs import Stub


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


class IsolateAttribute(object):
    def __init__(self, target, isolate_attr):
        self.target = target
        self.attr = isolate_attr

    def start(self):
        self.old = {}
        for name in dir(self.target):
            if name != self.attr:
                self.old[name] = getattr(self.target, name)
                setattr(self.target, name, Stub())

    def stop(self):
        for name, value in self.old.items():
            setattr(self.target, name, value)

    def __call__(self, fn):
        def decorator(func):
            @wraps(fn)
            def decorated(*args, **kwargs):
                with self as mod:
                    return fn(*args, **kwargs)
            return decorated

        return with_metadata(decorator)(fn)

    def __enter__(self):
        self.start()
        return self.target

    def __exit__(self, type, error, traceback):
        self.stop()


class Patcher(object):
    def __init__(self):
        self.getattr, self.setattr = getattr, setattr

    def object(self, name, attr, value=None):
        return Replace(name, attr, value or Stub(
            getattr(name, '__name__', '') + '.' + attr
        ))

    def __call__(self, modulepath, value=None):
        mod = __import__(modulepath)
        return self.object(mod, modulepath.rsplit('.', 1)[-1], value)

    def dict(self, current, new):
        return DictReplacement(current, new)

    def isolate(self, modulepath):
        modulepath, obj = modulepath.rsplit('.', 1)
        # replacing sys.module items doesn't affect anything, but we can mutate
        # the module object listed here to affect that given module.
        return IsolateAttribute(sys.modules[modulepath], obj)


patch = Patcher()



