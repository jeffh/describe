import sys
from types import ModuleType
from functools import wraps

from describe.spec.utils import Replace
from describe.mock.stubs import Stub


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
        # TODO: create decorator
        @wraps(fn)
        def decorator():
            with self as mod:
                return fn(mod)

        return decorator

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
        # replacing sys.module doesn't affect anything, but we can mutate
        # the module object listed here to affect that given module.
        return IsolateAttribute(sys.modules[modulepath], obj)


patch = Patcher()



