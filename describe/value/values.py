from number_value import NumberValue
from change_value import ChangeValue
import operator
from ..utils import ellipses, diff_iterables, is_iter, diff_dict, diff_iterable_str, diff_dict_str

class AssertionCore(object):
    def requires(self, assertion, message=None, **kwargs):
        # don't accidentally force EVAL if an exception was thrown
        if not self.lazy_eval_error:
            if 'value' not in kwargs:
                kwargs['value'] = self.value
            if 'value_name' not in kwargs:
                kwargs['value_name'] = getattr(self.value, '__name__', repr(self.value))
        else:
            if 'value' not in kwargs:
                kwargs['value'] = repr(self.raw_value)
            if 'value_name' not in kwargs:
                kwargs['value_name'] = getattr(self.raw_value, '__name__', repr(self.raw_value))
        if 'should' not in kwargs:
            kwargs['should'] = 'should'
        if message is not None:
            assert assertion, message % kwargs
        else:
            assert assertion
        return self
    # alias -- you should never override requires, but expect is overriden by NotValue
    expect = requires

# all internal APIs in the Value object go here
class ValueInternals(AssertionCore):
    REPR_MAX_LENGTH = 50
    def __init__(self, value, lazy=False):
        self.__value = value
        self.__lazy = lazy
        self.__lazy_eval_error = None

    def __repr__(self):
        if self.is_lazy:
            if self.lazy_eval_error:
                return "<Value: lazy_evaled(%s) with exceptions>" % self.__value.__name__
            return "<Value: lazy_eval(%s)>" % self.__value.__name__
        return "<Value: %s>" % ellipses(repr(self.__value), self.REPR_MAX_LENGTH)
        
    @property
    def lazy_eval_error(self):
        "Returns exception that occurred when trying to eval the value. Otherwise returns False."
        return self.__lazy_eval_error

    @property
    def is_lazy(self):
        "Returns True if this is a lazy value."
        return self.__lazy

    @property
    def raw_value(self):
        "Returns the raw value, unevaluated if it's lazy."
        return self.__value

    @property
    def value(self):
        "Returns the given value. Evaluates the wrapped value if lazy was set to True."
        if self.is_lazy:
            self.__lazy = False
            try:
                self.__value = self.__value()
            except Exception, e:
                self.__lazy_eval_error = e
                raise
        return self.__value

    @value.setter
    def value(self, val):
        self.__value = val

    def _new_value(self, val, lazy=False):
        """Returns a new instance that wraps the given value.

        If val is a function and lazy=True, then the argumentless function is invoked
        before the value is retrived.
        """
        return self.__class__(val, lazy)

    def _new_plain_value(self, val):
        "Ensures always a Value and not a NotValue instance."
        return self._new_value(val)

# Most core public API functions go here, many more in mixins.py
class BaseValue(ValueInternals):
    @property
    def should(self):
        """Returns the same value object.
        Use this method to make your statements readable.

        :returns: Same instance.
        :aliases: be, and_should

        .. seealso:: :attr:`~describe.value.Value.should_not`

        """
        return self # 'should' be enforced as a prefix? but for now this will do
    and_should = be = should


    def satisfy(self, func):
        """Provide a custom function for verification. Return False on failure or True on success."""
        if callable(func):
            self.expect(func(self.value), '%r failed to satisfy (%s)' % (
                self.value, func.__name__.replace('_', ' ')))
        else:
            def decorator(fun):
                self.expect(fun(self.value), func % {'value': self.value})
            return decorator

    @property
    def have(self):
        """Returns a NumberValue object for the length of the wrapped value."""
        return NumberValue(len(self.value), self.expect, format="len(%(value)r)")

    def be_close_to(self, value, delta=0.000001):
        """Like == operator, but accounts for error for floating point inaccuracies.

        :param value: Use assert that float values are equal, within a
            certain `delta`.
        :type value: float
        :param delta: The accept discrepancy/error allowed between the wrapped
            value and the provided value.
        :type delta: float
        :aliases: close_to

        Example::

            Value(1.0).should.be_close_to(1.0)

        """
        self.expect(abs(self.value - value) < delta,
            "%(value)r %(should)s == %(other)r +/- %(delta)r",
            other=value, delta=delta)
    close_to = be_close_to # alias

    def change(self, obj, attr=None, key=None):
        """Compares the changes in a specific attribute or key of `obj`.
        The attribute or key should be a type that support the subtraction
        operation.

        This is used to check if a function changed the given `obj`

        :param obj: The object to check for a change.
        :type obj: object
        :param attr: The attribute to access from the object: `getattr(obj, attr)`
        :type attr: str
        :param key: The key to access from the object: `obj[key]`
        :type key: str

        .. note::

            Value should be a function that changes an object.

        Example::

            s = {'a': 0}
            @Value
            def increment():
                s['a'] += 1
            increment.should.change(s, key='a').by(1)
        """
        chgVal = ChangeValue(obj, self.expect, attr=attr, key=key)
        self.value()
        chgVal.capture_value_as_new()
        chgVal.expect_values_to_be_not_equal()
        return chgVal

    def instance_of(self, the_type):
        """Checks if the type of the wrapped object is an instance of the given type.

        :param the_type: The class/type to compare the wrapped value's class type to.
        :type the_type: type
        :aliases: type_of

        Example::

            Value(2).should.be.instance_of(int)
            Value(2.2).should.be.type_of(float)

        """
        if isinstance(the_type, tuple):
            type_names = ', '.join( t.__name__ for t in the_type )
        else:
            type_names = the_type.__name__
        self.expect(isinstance(self.value, the_type),
            "%(value)r %(should)s be of type %(name)s instead of %(value_name)s",
            name=type_names, value_name=type(self.value).__name__)
    type_of = instance_of

    def have_attr(self, name):
        self.expect(hasattr(self.value, name),
            "%(value)r %(should)s have attribute %(name)s",
            name=name)
    have_attribute = have_attr

    #@property
    def true(self):
        """Expects the value to be logically true."""
        self.expect(bool(self.value), "%(value)r %(should)s logically True.")
    #@property
    def false(self):
        """Expects the value to be logically false."""
        self.expect(not self.value, "%(value)r %(should)s logically False.")

    def __eq__(self, other):
        expectation = self.value == other
        if isinstance(self.value, dict) and isinstance(other, dict):
            result = diff_dict(self.value, other)
            msg = "%(value)s %(should)s == %(other)s.\n\n%(diff)s"
            kwargs ={
                'other': ellipses(repr(other), self.REPR_MAX_LENGTH),
                'value': ellipses(repr(self.value), self.REPR_MAX_LENGTH),
                'diff': diff_dict_str(result),
            }
            self.expect(expectation, msg, **kwargs)
        elif is_iter(self.value) and is_iter(other) and not expectation:
            result = diff_iterables(self.value, other)
            msg = "%(value)s %(should)s == %(other)s.\n\n%(diff)s"
            kwargs = {
                'other': ellipses(repr(other), self.REPR_MAX_LENGTH),
                'value': ellipses(repr(self.value), self.REPR_MAX_LENGTH),
                'diff': diff_iterable_str(result),
            }

            self.expect(expectation, msg, **kwargs)
        else:
            self.expect(expectation, "%(value)s %(should)s == %(other)s.", other=other)

    def __ne__(self, other):
        self.expect(self.value != other, "%(value)r %(should)s != %(other)r.", other=other)

    def __lt__(self, other):
        self.expect(self.value < other, "%(value)r %(should)s < %(other)r.", other=other)

    def __le__(self, other):
        self.expect(self.value <= other, "%(value)r %(should)s <= %(other)r", other=other)

    def __gt__(self, other):
        self.expect(self.value > other, "%(value)r %(should)s > %(other)r", other=other)

    def __ge__(self, other):
        self.expect(self.value >= other, "%(value)r %(should)s >= %(other)r", other=other)

    def __nonzero__(self):
        self.expect(bool(self.value), "%(value)r %(should)s be logically True")
        return bool(self.value)

    def contain(self, item, *items):
        """Expects that the given `item` and `*items` be in the wrapped value.

        :param item: The item to check is contained in the wrapped value.
        :type item: object
        :param items: More items may be specified to check if they are in
            the wrapped object.

        This is identical to asserting for each item::

            assert obj in wrapped_value

        Alternatively, you may use the `in` keyword::

            2 in Value([1,2,3])

        Example usage::

            Value([1,2,3]).should.contain(1,2,3)

        """
        msg = "%(item)r %(should)s be in %(value)r"
        self.expect(item in self.value, msg, item=item)
        for i in items:
            self.expect(i in self.value, msg, item=i)
        return self

    def __contains__(self, item):
        self.contain(item)

    def __setitem__(self, key, value):
        raise Exception, "Value is unassignable. Did you mean ==?"

