import re

from describe.matchers.core import MatcherBase, matcher_repository


class TruthyMatcher(MatcherBase):
    MESSAGE = 'be true'
    METHODS = ['be_truthy']

    def match(self, actual):
        return bool(actual.evaluate())
matcher_repository.add(TruthyMatcher)


class FalsyMatcher(MatcherBase):
    MESSAGE = 'be false'
    METHODS = ['be_falsy']

    def match(self, actual):
        return not bool(actual.evaluate())
matcher_repository.add(FalsyMatcher)


class NoneMatcher(MatcherBase):
    MESSAGE = 'none'
    METHODS = ['be_none']

    def match(self, actual):
        return actual.evaluate() == None
matcher_repository.add(NoneMatcher)


class EqualityMatcher(MatcherBase):
    MESSAGE = 'be == %(expected)r'
    METHODS = ['__eq__']

    def match(self, actual, expected):
        return actual.evaluate() == expected
matcher_repository.add(EqualityMatcher)


# We need this class to hook into __ne__ method
class NonEqualityMatcher(MatcherBase):
    MESSAGE = 'be != %(expected)r'
    METHODS = ['__ne__']

    def match(self, actual, expected):
        return actual.evaluate() != expected
matcher_repository.add(NonEqualityMatcher)


class InstanceMatcher(MatcherBase):
    MESSAGE = 'be an instance of %(expected)r'
    METHODS = ['be_instance_of', 'be_an_instance_of']

    def get_postfix_message(self, actual):
        return self.MESSAGE % {
            'expected': self.expected_value.__name__,
            'actual': actual
        }

    def match(self, value, klass):
        return isinstance(value.evaluate(), klass)
matcher_repository.add(InstanceMatcher)


class SubclassMatcher(MatcherBase):
    MESSAGE = 'be a subclass of %(expected)r'
    METHODS = ['be_subclass_of', 'be_a_subclass_of']

    def match(self, subclass, parentclass):
        return issubclass(subclass.evaluate(), parentclass)
matcher_repository.add(SubclassMatcher)


class IsInMatcher(MatcherBase):
    MESSAGE = 'contain %(expected)r'
    METHODS = ['contain', 'include']

    def match(self, collection, item):
        return item in collection.evaluate()
matcher_repository.add(IsInMatcher)


class GreaterThanMatcher(MatcherBase):
    MESSAGE = 'be > %(expected)r'
    METHODS = ['__gt__']

    def match(self, a, b):
        return a.evaluate() > b
matcher_repository.add(GreaterThanMatcher)


class GreaterThanOrEqualToMatcher(MatcherBase):
    MESSAGE = 'be >= %(expected)r'
    METHODS = ['__ge__']

    def match(self, a, b):
        return a.evaluate >= b
matcher_repository.add(GreaterThanOrEqualToMatcher)

class LessThanMatcher(MatcherBase):
    MESSAGE = 'be < %(expected)r'
    METHODS = ['__lt__', 'be_lt', 'be_less_than']

    def match(self, a, b):
        return a.evaluate() < b
matcher_repository.add(LessThanMatcher)


class LessThanOrEqualToMatcher(MatcherBase):
    MESSAGE = 'be <= %(expected)r'
    METHODS = ['__le__']

    def match(self, a, b):
        return a.evaluate() <= b
matcher_repository.add(LessThanOrEqualToMatcher)


class ExceptionMatcher(MatcherBase):
    MESSAGE = 'raise error %(expected)r, but got %(error)s'
    FN_MESSAGE = 'raise error %(expected)r, but got %(error)s.\n\nDid you mean to do: expect(%(actual)s).with_args().to.raise_error(%(expected)s)?'
    METHODS = ['raise_error']

    def reads_as_name(self, obj):
        if self.is_class(obj) or callable(obj):
            return obj.__name__
        return repr(obj)

    def get_postfix_message(self, actual_value):
        if callable(actual_value):
            msg = self.MESSAGE
        else:
            msg = self.FN_MESSAGE
        return msg % {
            'expected': self.reads_as_name(self.expected_value),
            'actual': actual_value,
            'error': self.reads_as_name(getattr(self, 'error', None)),
        }

    def is_class(self, error):
        return type(error) == type

    def error_equal(self, error1, error2):
        return error1 == error2 or (type(error1) == type(error2) and str(error1) == str(error2))

    def match(self, fn, exception):
        try:
            fn.evaluate()
        except Exception as e:
            self.error = e
            if self.is_class(exception):
                return isinstance(e, exception)
            else:
                return self.error_equal(e, exception)
        return False
matcher_repository.add(ExceptionMatcher)


class IsMatcher(MatcherBase):
    MESSAGE = 'be equal to %(expected)r'
    METHODS = ['be_equal', 'be_equal_to']

    def match(self, a, b):
        return a.evaluate() is b
matcher_repository.add(IsMatcher)


class BeCloseToMatcher(MatcherBase):
    MESSAGE = 'be close to %(expected)r (+- %(error)f)'
    METHODS = ['be_close_to', 'be_close', 'be_near_to', 'be_near']

    def __init__(self, value, acceptability=0.00001):
        super(BeCloseToMatcher, self).__init__(value)
        self.error = acceptability

    def get_postfix_message(self, actual_value):
        return self.MESSAGE % {
            'expected': self.expected_value,
            'actual': actual_value,
            'error': self.error,
        }

    def match(self, a, b):
        return abs(a.evaluate() - b) <= self.error
matcher_repository.add(BeCloseToMatcher)


class MatchesMatcher(MatcherBase):
    MESSAGE = 'match regular expression %(expected)r'
    METHODS = ['match']

    def __init__(self, value, flags=0):
        super(MatchesMatcher, self).__init__(value)
        self.flags = flags

    def match(self, string, regexp):
        return re.search(regexp, string.evaluate(), self.flags)
matcher_repository.add(MatchesMatcher)


class HaveSubsetMatcher(MatcherBase):
    MESSAGE = 'have subset %(expected)r'
    METHODS = ['have_subset']

    def match(self, superdict, subdict):
        superdict = superdict.evaluate()
        assert isinstance(superdict, dict) and isinstance(subdict, dict), 'actual <%(actual)r> and expected <%(expected)r> should be of type dict' % {
            'actual': superdict,
            'expected': subdict,
        }
        for key, value in subdict.items():
            if key not in superdict or superdict[key] != value:
                return False
        return True
matcher_repository.add(HaveSubsetMatcher)


class HaveAttrMatcher(MatcherBase):
    MESSAGE = 'have attribute %(expected)r'
    METHODS = ['have_attr']

    def match(self, obj, attr):
        return hasattr(obj.evaluate(), attr)
matcher_repository.add(HaveAttrMatcher)


class BeCallableMatcher(MatcherBase):
    MESSAGE = 'be callable.'
    METHODS = ['be_callable']

    def match(self, actual):
        return callable(actual.evaluate())
matcher_repository.add(BeCallableMatcher)
