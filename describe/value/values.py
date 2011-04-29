from number_value import NumberValue
from change_value import ChangeValue

class AssertionCore(object):
    def requires(self, assertion, message=None, **kwargs):
        # don't accidentally force EVAL if an exception was thrown
        if not self.lazy_eval_error:
            kwargs['value'] = self.value
            kwargs['value_name'] = getattr(self.value, '__name__', str(self.value))
        else:
            kwargs['value'] = repr(self.raw_value)
            kwargs['value_name'] = getattr(self.raw_value, '__name__', str(self.raw_value))
        if 'should' not in kwargs:
            kwargs['should'] = 'should'
        if message is not None:
            assert assertion, message % kwargs
        else:
            assert assertion
    # alias -- you should never override requires, but expect is overriden by NotValue
    expect = requires

# all internal APIs in the Value object go here
class ValueInternals(AssertionCore):
    def __init__(self, value, lazy=False):
        self.__value = value
        self.__lazy = lazy
        self.__lazy_eval_error = None

    def __repr__(self):
        if self.is_lazy:
            if self.lazy_eval_error:
                return "<Value: lazy_evaled(%s) with exceptions>" % self.__value.__name__
            return "<Value: lazy_eval(%s)>" % self.__value.__name__
        return "<Value: %r>" % repr(self.__value)
        
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
        """Returns the same value object. Use this method to make your statements readable."""
        return self # 'should' be enforced as a prefix? but for now this will do
    be = should
    
        
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
        """Like == operator, but checks +- offset for floating point inaccuracies."""
        self.expect(abs(self.value - value) < delta,
            "%(value)r %(should)s == %(other)r +/- %(delta)r",
            other=value, delta=delta)
    close_to = be_close_to # alias
            
    def change(self, obj, attr=None, key=None):
        """Compares the changes in the value.
        
        Value should be a function that changes an object.
        >>> s = {'a': 0}
        >>> @Value
        ... def increment():
        ...     s['a'] += 1
        ... increment.should.change(s, key='a').by(1)
        """
        chgVal = ChangeValue(obj, self.expect, attr=attr, key=key)
        self.value()
        chgVal.capture_value_as_new()
        chgVal.expect_values_to_be_not_equal()
        return chgVal
        
    def instance_of(self, klass):
        "Checks type of the wrapped object to the given class."
        self.expect(isinstance(self.value, klass),
            "%(value)r %(should)s be of class %(name)s instead of %(value_name)s",
            name=klass.__name__, value_name=type(self.value).__name__)
    type_of = instance_of
    
    def have_attr(self, name):
        self.expect(hasattr(self.value, name),
            "%(value)r %(should)s have attribute %(name)s",
            name=name)
    have_attribute = have_attr
    
    #@property
    def true(self):
        self.expect(bool(self.value), "%(value)r %(should)s logically True.")
    #@property
    def false(self):
        self.expect(not bool(self.value), "%(value)r %(should)s logically False.")
    
    def __eq__(self, other):
        self.expect(self.value == other, "%(value)r %(should)s == %(other)r.", other=other)
    
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
    
    def contain(self, item):
        self.expect(item in self.value, "%(item)r %(should)s be in %(value)r", item=item)
    
    def __contains__(self, item):
        self.expect(item in self.value, "%(item)r %(should)s be in %(value)r", item=item)
    
    def __setitem__(self, key, value):
        raise Exception, "Value is unassignable. Did you mean ==?"
