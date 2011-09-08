"""Provides the extensive feature set for the Value objects. It can be assumed that all are
mixed into the ValueInternals object.
"""

from properties import Properties
from decorators import VerifyDecorator, DeferredDecorator
from ..tracebacks import get_current_stack, get_stack
from ..mixins import OperatorsMixin, ReverseOperatorsMixin, InplaceOperatorsMixin, \
    BuiltinFunctionsMixin
from ..utils import is_iter, diff_iterables, ellipses
import re
try:
    set
except ValueError:
    from sets import Set as set

__ALL__ = ['OperatorsMixin', 'BuiltinFunctionsMixin', 'PropertyMixin', 'InvokerMixin', 'NotMixin', 'EnumerableMixin', 'CollectionMixin']

class OperatorsMixin(OperatorsMixin, ReverseOperatorsMixin, InplaceOperatorsMixin):
    """All operators return new lazy Value object after operating on the wrapped value object."""
    def _lazy_value(self, a, b, func, single_arg=False):
        lamb = lambda: func(a.value,b)
        if single_arg:
            lamb = lambda: func(a.value)
        return self._new_value(lamb, lazy=True)
    ReversedOperatorProcessor = OperatorProcessor = _lazy_value

    def _inplace_lazy_value(self, a, b, func):
        a.value = func(a.value, b)
        return a
    InplaceOperatorProcessor = _inplace_lazy_value

class BuiltinFunctionsMixin(BuiltinFunctionsMixin):
    """All builtin hooks return a new lazy value object when possible.

    If cannot return a new object (due to constraints of the hook, they are actively eval'ed)
    """
    def _builtin_function_processor(self, obj, typefn):
        f = lambda: typefn(obj.value)
        return self._new_value(f, lazy=True)
    BuiltinFunctionProcessor = _builtin_function_processor
    # TODO: figure out of wrapping these values are acceptable
    # or some value, based operation is acceptable
    def __enter__(self):                  return self.value.__enter__()
    def __exit__(self, type, val, trace): return self.value.__exit__(type, val, trace)

class StringMixin(object):
    """String specific methods."""
    def requires_string(self):
        """Internal. Enforces the provided type to be a string."""
        prev_stack = get_current_stack()[1]
        self.requires(type(self.value) == str,
            "Value(%(value)r).%(method)s %(should)s be type str, but was type %(actual)s.",
            method=prev_stack.name, actual=type(self.value).__name__)

    def match(self, regex):
        """Performs a regular expression match expectation.
        The wrapped value is expected to be a string.

        """
        self.requires_string()
        self.expect(re.search(regex, self.value),
            "%(regex)r.search(%(value)r) %(should)s return a match.",
            regex=regex)

class CollectionMixin(object):
    def have_keys(self, key, *keys):
        for k in (key,) + keys:
            try:
                self.value[k]
            except (IndexError, KeyError):
                self.expect(False, "%(key)r not found in %(value)r", key=k)

    have_key = have_keys

class EnumerableMixin(object):
    """Enumerable specific methods."""
    def iter_as_values(self):
        """Converts each element of the wrapped value as a Value object.

        Example::

            for i,v in enumerate(Value([1,2,3]).iter_as_values()):
                v.should == i

        .. seealso:: :meth:`~describe.value.Value.iterate`

        """
        self.enumerable()
        return iter(map(self._new_value, self.value))

    def enumerable(self):
        """Expects that the wrapped value can be enumerated using iter().

        Example::

            Value([1,2,3]).should.be.enumerable

        """
        self.expect(is_iter(self.value), "%(value)r %(should)s be enumerable.")

    def have_equal_elements_to(self, other):
        """Expects that the given elements appear in the same order as the
        wrapped value.

        :param other: The in-order elements to compare to the wrapped values.
        :type other: iter

        This is identical to doing::

            tuple(wrapped_value) == tuple(other)

        Example::

            Value([1,2,3]).should.have_equals_elements_to((1,2,3))

        """
        self.enumerable()
        self.expect(is_iter(other), "value.has_equal_elements_to(%(other)r) should be iterable.", other=other)
        result = diff_iterables(self.value, other)
        msg = "%(value)s %(should)s have equal elements to %(other)s.\n\n%(diff)s"
        kwargs = {
            'other': ellipses(repr(other), self.REPR_MAX_LENGTH),
            'value': ellipses(repr(self.value), self.REPR_MAX_LENGTH),
            'diff': 'At element %(i)d:\n%(x)r\nshould equal to\n%(y)r' % \
                (result or {}),
        }
        self.expect(result is None, msg, **kwargs)

    @classmethod
    def iterate(cls, enumerables):
        """Alias to Value(enumerables).iter_as_values().

        .. seealso:: :meth:`~describe.value.Value.iter_as_values`

        """
        return cls(enumerables).iter_as_values()

class PropertyMixin(object):
    """Allows getting/setting methods of the wrapped object."""
    @property
    def invoking(self):
        """Returns an object that allows you to access attributes of the object Value wraps.

        Invoke implies a method call. Use get to imply a property access.
        """
        return Properties(self.value, self._new_value, lazy=True)
    invoke = invoking

    @property
    def get(self):
        "Alias to invoke, but implies reading an attribute (instead of a method)."
        return self.invoke
    getting = get
    # too unpredicable, and difficult to debug.
    #def __getattr__(self, key):
    #    print self
    #    return self._new_value(getattr(self.value, key))
    #
    #def __getitem__(self, key):
    #    return self._new_value(self.value[key])


class InvokerMixin(object):
    """Allows invocation of methods of the wrapped object."""
    def __init__(self, *args, **kwargs):
        super(InvokerMixin, self).__init__(*args, **kwargs)

    @property
    def return_value(self):
        """Forces the evaluation of a lazy value. Raises TypeError if not lazy."""
        if not self.is_lazy:
            raise TypeError, "No function specified."
        return self._new_value(self.value)

    def __call__(self, *args, **kwargs):
        """Creates a new lazy Value object of the wrapped value with *args and **kwargs."""
        if not callable(self.value):
            self.expect(False, "%(value)r should callable.", method=method_name)
        return self._new_value(DeferredDecorator(self.value, args, kwargs), lazy=True)

    def raise_error(self, exception_class, str_or_re=None):
        """Expects the raising of a given exception class and an optional message to match."""
        #self.expect(not (self.is_lazy or callable(self.value)),
        #    "%(value_name)r %(should)s be callable.")
        try:
            return_value = self.value # lazy eval
            self.expect(False, "Calling %(value_name)r %(should)s throw %(exception)r",
                exception=exception_class.__name__)
            return VerifyDecorator(None)
        except AssertionError:
            raise # assertion errors will always bubble up
        except Exception, e:
            self.expect(type(e) == exception_class,
                "%(value_name)r %(should)s throw %(exception)r",
                exception=exception_class.__name__)
            if str_or_re is not None:
                if isinstance(str_or_re, str):
                    self.expect(e.message.find(str_or_re) != -1,
                        "%(value_name)r %(should)s find given text in %(exception)s.message str",
                        exception=exception_class.__name__)
                elif hasattr(str_or_re, 'search'):
                    self.expect(str_or_re.search(e.message) != None,
                        "%(value_name)r %(should)s find given regex in %(exception)s.message str",
                        exception=exception_class.__name__)
            return VerifyDecorator(e)

class NotMixin(object):
    """Like BaseValue, but is inverse NOT operations."""
    @property
    def should_not(self):
        return self._new_plain_value(self.__value)
    and_should_not = should_not

    def change(self, obj, attr):
        chgVal = ChangeValue(obj, attr, self.expect)
        self.value()
        chgVal.capture_value_as_new()
        chgVal.expect_values_to_be_equal()
        return self # if we can't change value, we can't change by a specified amount.

    # all other methods use this method to create assertions
    def expect(self, assertion, message=None, **kwargs):
        if 'should' not in kwargs:
            kwargs['should'] = 'should not'
        return super(NotMixin, self).expect(not assertion, message, **kwargs)
