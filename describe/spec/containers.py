import sys
import traceback
from unittest import FunctionTestCase, TestSuite
from itertools import izip_longest
from cStringIO import StringIO

from describe.spec.utils import CallOnce, accepts_arg, func_equal, tabulate
from describe import run


class SpecFile(object):
    "Represents a file that will be inspected for specs to run."
    def __init__(self, filepath, modulepath, module):
        self.filepath, self.modulepath = filepath, modulepath
        self.module = module
        self.__hashcode = None

    def __hash__(self):
        if self.__hashcode is None:
            self.__hashcode = hash(self.filepath) ^ hash(self.modulepath)
        return self.__hashcode

    def __repr__(self):
        return '<SpecFile: %(modulepath)s (%(filepath)r)>' % {
            'filepath': self.filepath,
            'modulepath': self.modulepath,
        }


class Context(object):
    """An object that the test functions can use to pass data to each other.

    All public methods are prefixed with an underscore to avoid conflicts.
    """
    def __init__(self, items=None, properties=None, parent=None):
        self._items = dict(items or {})
        self._properties = dict(properties or {})
        self._parent = parent
        super(self.__class__, self).__init__()

    def inject_into_self(self, fn):
        # inject into self
        if getattr(fn, 'im_self', None):
            props = self._combined_properties()
            for name, value in props.items():
                setattr(fn.im_self, name, value)

    def __getitem__(self, name):
        if name not in self._items and self._parent:
            return self._parent[name]
        return self._items[name]

    def __delitem__(self, name):
        del self._items[name]

    def __setitem__(self, name, value):
        self._items[name] = value

    def __getattr__(self, name):
        if name not in self._properties and self._parent:
            return getattr(self._parent, name)
        return self._properties[name]

    def __setattr__(self, name, value):
        if name in ('_items', '_properties', '_parent'):
            super(self.__class__, self).__setattr__(name, value)
        else:
            self._properties[name] = value

    def __delattr__(self, name):
        del self._properties[name]

    def __iter__(self):
        return set(self._items.keys() + iter(self._parent))

    def _update_properties(self, newproperties):
        self._properties.update(newproperties)

    def _combined_properties(self):
        """Returns a dictionary with this object's properties merged with all its parent's
        properties.

        The returned dictionary is all the available properties for this object (and their
        associated values).
        """
        result = dict(self._properties)
        par = self._parent
        while par:
            result.update(par._properties)
            par = par._parent
        return result

    def _combined_items(self):
        """Returns a dictionary with this object's properties merged with all its parent's
        properties.

        The returned dictionary is all the available properties for this object (and their
        associated values).
        """
        result = dict(self._items)
        par = self._parent
        while par:
            result.update(par._items)
            par = par._parent
        return result

    def __repr__(self):
        return "<%s(%r)[%r]>" % (
            self.__class__.__name__,
            self._combined_properties(),
            self._combined_items(),
        )


class Failure(object):
    "Represents the state of an Example when an error occurred running it."
    def __init__(self, error, traceback, stdout=None, stderr=None):
        self.error = error
        self.traceback = traceback
        self.stdout = stdout
        self.stderr = stderr

    def __repr__(self):
        return "Failure(%r, %r, %r, %r)" % (
            self.error, self.traceback, self.stdout, self.stderr
        )

    def __eq__(self, other):
        return type(self.error) == type(other.error) and self.error.message == other.error.message and \
            self.traceback == other.traceback and self.stdout == other.stdout and self.stderr == other.stderr

    def __ne__(self, other):
        return not (self == other)


class Example(object):
    "Represents an individual behavior to test."
    def __init__(self, testfn, before=(), after=(), parents=None, user_time=-1, real_time=-1,
            error=None, traceback=None, stdout=None, stderr=None):
        self.testfn = testfn
        self._before = self._filter_callables(before)
        self._after = self._filter_callables(after)
        self.parents = tuple(parents or ())
        self.traceback = traceback
        self.error = error
        self.user_time = user_time
        self.real_time = real_time
        self.stdout = stdout
        self.stderr = stderr

    def unittest_equiv(self, context):
        return FunctionTestCase(self.testfn,
                lambda: self.before(context),
                lambda: self.after(context))
    @property
    def name(self):
        return getattr(self.testfn, '__name__', None) or str(self.testfn)


    def __repr__(self):
        return '%s(%s, \n%r)' % (self.__class__.__name__, self.name, self.testfn)
        #return "%s(%r, %r, %r, %r)" % (
        #    self.__class__.__name__, self.testfn, self._before, self._after, self.parents
        #)

    def __eq__(self, other):
        return self.testfn.__module__ == other.testfn.__module__ and self.testfn.__name__ == other.testfn.__name__

    def __nonzero__(self):
        return 1

    def __len__(self):
        return 0

    def before(self, context):
        "Invokes all before functions with context passed to them."
        run.before_each.execute(context)
        self._invoke(self._before, context)

    def after(self, context):
        "Invokes all after functions with context passed to them."
        self._invoke(self._after, context)
        run.after_each.execute(context)

    def _invoke(self, funcs, context):
        assert context, "Context needs to be provided for Example to run."

        for fn in funcs:
            if accepts_arg(fn):
                fn(context)
            else:
                context.inject_into_self(fn)
                fn()

    def _filter_callables(self, fns):
        return list(filter(callable, fns))


class ExampleGroupTestSuite(TestSuite):
    "Represents an Example Group as a unittest's Test Suite."
    def __init__(self, tests, before_all, after_all, parents=None):
        super(self.__class__, self).__init__(tests)
        self._before_all, self._after_all = before_all, after_all

    def run(self, *args, **kwargs):
        self._before_all()
        try:
            result = super(self.__class__, self).run(*args, **kwargs)
        finally:
            self._after_all()
        return result


class ExampleGroup(Example):
    "Represents a collection of examples to run."
    def __init__(self, obj, before=(), after=(), parents=None, examples=None, user_time=-1,
            real_time=-1, error=None, traceback=None):
        self.examples = list(examples or [])
        super(ExampleGroup, self).__init__(
            obj, [CallOnce(before)], [CallOnce(after)], parents,
            user_time, real_time, error, traceback, None, None
        )

    def unittest_equiv(self, context):
        return ExampleGroupTestSuite(
            [ex.unittest_equiv(context) for ex in self.examples],
            lambda: self.before(context),
            lambda: self.after(context)
        )

    def __repr__(self):
        return "%s(%s, %s, \n%s)" % (
            self.__class__.__name__, self.name, self.parents,
            tabulate('\n'.join(map(repr, self.examples)))
        )

    def __eq__(self, other):
        return self.examples == getattr(other, 'examples', None)#and super(ExampleGroup, self).__eq__(other)

    def __iter__(self):
        return iter(self.examples)

    def __len__(self):
        return len(self.examples)

    def __getitem__(self, key):
        return self.examples[key]

    def append(self, example):
        if example not in self:
            self.examples.append(example)
        return self

    def remove(self, example):
        self.examples.remove(example)

    def __contains__(self, example):
        return example in self.examples

