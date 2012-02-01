from collections import defaultdict
from functools import wraps

from describe.flags import INIT, NO_ARG


class MatcherBase(object):
    METHODS = []
    def __init__(self, expected_value=NO_ARG):
        self.expected_value = expected_value

    def get_postfix_message(self, actual_value):
        return self.MESSAGE % {'expected': self.expected_value, 'actual': actual_value}

    def get_methods(self):
        "Used by the method repository to determine what methods to add to wrapper objects."
        if not self.METHODS:
            raise NotImplementedError('No methods for this matcher.')
        return self.METHODS

    def match(self, actual_value, expected_value):
        """Should be overridden by subclasses. Returns a boolean value to assert.

        Wrapper objects handle the negation of the assertion.
        """
        raise NotImplementedError('Match method not implemented in subclass: %r' % self.__class__)

    def asserts(self, *args, **kwargs):
        """Wraps match method and places under an assertion. Override this for higher-level control,
        such as returning a custom object for additional validation (e.g. expect().to.change())
        """
        result = self.match(*args, **kwargs)
        self.expect(result)
        return result

    def __call__(self, actual_value, expect):
        """Main entry point for assertions (called by the wrapper).
        expect is a function the wrapper class uses to assert a given match.
        """
        self._expect = expect
        if self.expected_value is NO_ARG:
            return self.asserts(actual_value)
        return self.asserts(actual_value, self.expected_value)

    def expect(self, assertion, matcher=None):
        self._expect(assertion, matcher or self)

    @classmethod
    def as_function(cls):
        """Returns this matcher as function to run as an independent matcher.
        Functions are invoked like: expect(2).to(be_true())
        """
        return cls

class FunctionMatcher(MatcherBase):
    def __init__(self, expected, fn, message='', methods=()):
        self.expected_value = expected
        self.message = message or (fn.__name__ + ' %(expected)r')
        self.fn = fn
        self.METHODS = list(methods) or []

    def get_postfix_message(self, actual_value):
        return self.message % {'expected': self.expected_value, 'actual': actual_value}

    def match(self, actual, expected):
        return self.fn(actual, expected)

def matcher(expects_to='', methods=None):
    method_names = [methods]
    def _decorator(fn):
        if method_names[0] is None:
            method_names[0] = (fn.__name__,)
        return wraps(fn)(lambda expected: FunctionMatcher(expected, fn, expects_to, method_names[0]))
    return _decorator

class MatcherRepository(object):
    def __init__(self):
        self.clear()

    def __repr__(self):
        return repr(self.methods)

    def add(self, matcher):
        if matcher in self.matchers:
            return
        for name in matcher(INIT).get_methods():
            self.methods[name].append(matcher)
        self.matchers.add(matcher)

    def remove(self, matcher):
        for name in matcher(INIT).get_methods():
            self.methods[name].remove(matcher)
        self.matchers.remove(matcher)

    def clear(self):
        self.matchers = set()
        self.methods = defaultdict(list)

    def add_iter(self, matchers_iter):
        "Loads all available matchers."
        for obj in matchers_iter:
            self.add(obj)

    @property
    def method_names(self):
        return self.methods.keys()

    def __contains__(self, method_name):
        return method_name in self.methods

    def __getitem__(self, method_name):
        try:
            return self.methods[method_name][0]
        except IndexError:
            raise KeyError("No matchers found for %r" % method_name)


matcher_repository = MatcherRepository()
