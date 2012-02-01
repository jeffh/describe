# various kinds of objects that wrap values
from describe.matchers.core import matcher_repository
from describe.matchers.core import matcher as matcher_decorator
from describe.flags import NO_ARG


def humanize(name):
    "Returns a human-friendly version of a given name (for a matcher)."
    return name.lower().replace('_matcher', '').replace('Matcher', '').replace('_', ' ')


class ValueWrapper(object):
    def __init__(self, value, args=None, kwargs=None):
        self.raw_value = value.evaluate() if isinstance(value, self.__class__) else value
        self.args, self.kwargs = args, kwargs
        if self.args is not None and self.kwargs is not None:
            if not callable(value):
                raise TypeError('%r is not callable' % type(value))

    def __repr__(self):
        if callable(self.raw_value):
            if self.args is None or self.kwargs is None:
                raise TypeError("expects invocation of callable using the with_args() method.")
            args = [
                ', '.join(map(repr, self.args)),
                ', '.join('%r=%r' % item for item in self.kwargs.items())
            ]
            args = [i for i in args if i.strip() != '']
            return 'invocation of %s(%s)' % (
                self.raw_value.__name__,
                ', '.join(args)
            )
        return repr(self.raw_value)

    def evaluate(self):
        if self.args is not None and self.kwargs is not None:
            return self.raw_value(*self.args, **self.kwargs)
        return self.raw_value


class WrapperBase(object):
    def __init__(self, value, parent=None):
        if isinstance(value, ValueWrapper):
            self.actual_value = value
        else:
            self.actual_value = ValueWrapper(value)
        self.parent = parent

    def get_name(self):
        return getattr(self, 'NAME', humanize(self.__class__.__name__))

    def with_name(self, name):
        self.NAME = name
        if name is None:
            del self.NAME
        return self

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.actual_value)

    def get_assertion_message(self, postfix=''):
        sb = [self.get_name()]
        n = self.parent
        while n:
            sb.append(n.get_name())
            n = n.parent
            sb.reverse()
        return ' '.join(sb) + ' ' + postfix

    def __enter__(self):
        raise TypeError("with statement is not supported on this object.")

    def __exit__(self):
        pass


class UsesMatchers(object):
    IS_NEGATED = False
    def __getattr__(self, attrname):
        if attrname in matcher_repository:
            def invoke_matcher(expected=NO_ARG, *args, **kwargs):
                if expected is NO_ARG:
                    matcher = matcher_repository[attrname](*args, **kwargs)
                else:
                    matcher = matcher_repository[attrname](expected, *args, **kwargs)
                return matcher(self.actual_value, self.__expect)
            return invoke_matcher
        raise AttributeError('%r object has not attribute %r' % (self.__class__, attrname))

    def __expect(self, assertion, matcher):
        if hasattr(matcher, 'get_postfix_message'):
            postfix = matcher.get_postfix_message(self.actual_value)
        elif hasattr(matcher, 'postfix_message'):
            postfix = matcher.postfix_message % {'actual': self.actual_value}
        else:
            postfix = humanize(matcher.__name__)

        if self.IS_NEGATED:
            assert not assertion, self.get_assertion_message(postfix)
        else:
            assert assertion, self.get_assertion_message(postfix)

    def __call__(self, matcher):
        return matcher(self.actual_value, self.__expect)

    def __eq__(self, other): return self.__getattr__('__eq__')(other)
    def __ne__(self, other): return self.__getattr__('__ne__')(other)
    def __gt__(self, other): return self.__getattr__('__gt__')(other)
    def __ge__(self, other): return self.__getattr__('__ge__')(other)
    def __lt__(self, other): return self.__getattr__('__lt__')(other)
    def __le__(self, other): return self.__getattr__('__le__')(other)


class To(UsesMatchers, WrapperBase):
    pass


class ToNot(UsesMatchers, WrapperBase):
    # TODO: get WrapperBase to autoconvert this name from the class instead of
    # manually specifying it here. This should be automatic.
    NAME = 'to not'
    IS_NEGATED = True


class ExceptionBlock(object):
    def __init__(self, callback):
        self.callback = callback

    def __enter__(self):
        pass

    def __exit__(self, type, value, traceback):
        return self.callback(value)


class Expectation(WrapperBase):
    def with_args(self, *args, **kwargs):
        return Expectation(ValueWrapper(self.actual_value.raw_value, args, kwargs), parent=self.parent)

    def __call__(self, *args, **kwargs):
        return self.with_args(*args, **kwargs)

    def __eq__(self, other): return self.to == (other)
    def __ne__(self, other): return self.to != (other)
    def __gt__(self, other): return self.to > (other)
    def __ge__(self, other): return self.to >= (other)
    def __lt__(self, other): return self.to < (other)
    def __le__(self, other): return self.to <= (other)

    @classmethod
    def to_raise_error(cls, error):
        def verify(err):
            def reraise():
                if err is not None:
                    raise err
            return cls(reraise).with_args().to.raise_error(error)
        return ExceptionBlock(verify)
    to_raise = raise_error = to_raise_error

    @classmethod
    def add_matcher(cls, fn):
        matcher_repository.add(fn)

    @classmethod
    def remove_matcher(cls, fn):
        matcher_repository.remove(fn)

    @property
    def to(self):
        return To(self.actual_value, parent=self)

    @to.setter
    def to(self, value):
        raise SyntaxError('expect(%r).to cannot be be assigned. Did you mean ==?' % self.actual_value)

    @property
    def to_not(self):
        return ToNot(self.actual_value, parent=self)

    @to_not.setter
    def to_not(self, value):
        raise SyntaxError('expect(%r).to_not cannot be be assigned. Did you mean ==?' % self.actual_value)

    def get_name(self):
        return 'expected %r' % self.actual_value
