import nose
import os
import unittest
from spec import Spec
try:
    set
except ValueError:
    from sets import Set as set

class SpecSelector(nose.selector.Selector):
    def wantDirectory(self, dirname):
        parts = set(dirname.lower().split(os.path.sep))
        for prefix in ('spec', 'specs', 'test', 'tests'):
            if prefix in parts:
                return True
        return False

    def wantFile(self, filename):
        parts = filename.lower().split(os.path.sep)
        base, ext = os.path.splitext(parts[-1])
        parts = set(parts)
        if ext != '.py':
            return False
        if 'spec' in base or 'test' in base:
            return True
        for prefix in ('spec', 'specs', 'test', 'tests'):
            if prefix in parts:
                return True
        return False

    def wantModule(self, module):
        return True

    def wantFunction(self, func):
        name = func.__name__
        if name.startswith('it') or name.startswith('test'):
            return True
        return None

    def wantClass(self, cls):
        return issubclass(cls, Spec) or cls.__name__.lower().startswith('describe') or \
            issubclass(cls, unittest.TestCase)

    def wantMethod(self, method):
        name = method.__name__
        if name.startswith('it') or name.startswith('should') or name.startswith('test'):
            return True
        return None

class SpecPlugin(nose.plugins.Plugin):
    name = "SpecLoader"
    enabled = True
    def configure(self, options, conf):
        pass
    def prepareTestLoader(self, loader):
        loader.selector = SpecSelector(loader.config)
