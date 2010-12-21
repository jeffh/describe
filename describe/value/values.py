
class NumberValue(object):
    def __init__(self, value, expect, format="%(value)r"):
        self.value = value
        self.expect = expect
        self.format = format

    def __call__(self, amount):
        self.expect(self.value == amount,
            (self.format+" %(should)s == %(amount)s"), amount=amount)
        return self
    
    @property
    def items(self):
        return None

    @property
    def elements(self):
        return None

    def at_least(self, amount):
        self.expect(self.value >= amount,
            (self.format+" %(should)s >= %(amount)s"), amount=amount)
        return self

    def at_most(self, amount):
        self.expect(self.value >= amount,
            (self.format+" %(should)s >= %(amount)s"), amount=amount)
        return self

class ChangeValue(object):
    "Represents a change in value by Value.should.change."
    def __init__(self, obj, attr, expect):
        self.obj, self.attr = obj, attr
        self.type = type(obj)
        self.old, self.new = self.capture_value(), None
        # remember, expect's value is the dirty function that was invoked
        self.expect = expect
    
    @property
    def attr_name(self):
        if callable(self.obj) and self.attr is None:
            return "%s" % (self.obj.__name__)
        return "%s.%s" % (self.type.__name__, self.attr)
    
    def capture_value(self):
        if callable(self.obj) and self.attr is None:
            return self.obj()
        return getattr(self.obj, self.attr)
        
    def capture_value_as_new(self):
        self.new = self.capture_value()
        
    def expect_values_to_be_not_equal(self):
        self.expect(self.old != self.new,
            "%(value_name)s %(should)s change %(target)s",
            target=self.attr_name)

    def expect_values_to_be_equal(self):
        self.expect(self.old == self.new,
            "%(value_name)s %(should)s change %(target)s",
            target=self.attr_name)
    
    @property
    def by(self):
        return NumberValue(abs(self.old - self.new), self.expect,
            format="abs("+str(self.old)+" - "+str(self.new)+") = %(value)r")
    """
    def by(self, num):
        self.expect(abs(self.old - self.new) == num,
            "%(value_name)s %(should)s change %(target)s by %(num)r instead of %(diff)r.",
            target=self.attr_name, num=num, diff=abs(self.old-self.new))
        return self
    
    def by_at_least(self, num):
        self.expect(abs(self.old - self.new) >= num,
            "%(value_name)s %(should)s change %(target)s by at least %(num)r instead of %(diff)r",
            target=self.attr_name, num=num, diff=abs(self.old-self.new))
        return self
    
    def by_at_most(self, num):
        self.expect(abs(self.old - self.new) <= num,
            "%(value_name)s %(should)s change %(target)s by at most %(num)r instead of %(diff)r",
            target=self.attr_name, num=num, diff=abs(self.old-self.new))
        return self
    """
            
    def starting_from(self, value):
        self.expect(self.old == value, 
            "%(value_name)s %(should)s start from %(expected)r, instead of %(old)r, at %(target)s",
            target=self.attr_name, expected=value, old=self.old)
        return self
    
    def to(self, value):
        self.expect(self.new == value,
            "%(value_name)s %(should)s become %(expected)r," +
            " instead of %(new)r, at %(target)s",
            target=self.attr_name, expected=value, new=self.new)
        return self

# all internal APIs in the Value object go here
class ValueInternals(object):
    def __init__(self, value, lazy=False):
        self.__value = value
        self.__lazy = lazy
        self.__lazy_eval_error = False

    def __repr__(self):
        if self.is_lazy:
            if self.lazy_eval_error:
                return "<Value: lazy_evaled(%s) with exceptions>" % self.__value.__name__
            return "<Value: lazy_eval(%s)>" % self.__value.__name__
        return "<Value: %r>" % repr(self.__value)
        
    @property
    def lazy_eval_error(self):
        return self.__lazy_eval_error

    @property
    def is_lazy(self):
        return self.__lazy

    @property
    def raw_value(self):
        return self.__value

    @property
    def value(self):
        if self.is_lazy:
            self.__lazy = False
            try:
                self.__value = self.__value()
            except Exception:
                self.__lazy_eval_error = True
                raise
        return self.__value

    @value.setter
    def value(self, val):
        self.__value = val

    def _new_value(self, val, lazy=False):
        return self.__class__(val, lazy)

    def _new_plain_value(self, val):
        "Ensures always a Value and not a NotValue instance."
        return self._new_value(val)

# Most core public API functions go here, many more in mixins.py
class BaseValue(ValueInternals):
    def expect(self, assertion, message=None, **kwargs):
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
    
    @property
    def should(self):
        return self # 'should' be enforced as a prefix? but for now this will do
    
    @property
    def be(self):
        return self
        
    def satisfy(self, func):
        if callable(func):
            self.expect(func(self.value), '%r failed to satisfy (%s)' % (
                self.value, func.__name__.replace('_', ' ')))
        else:
            def decorator(fun):
                self.expect(fun(self.value), func % {'value': self.value})
            return decorator
        
    @property
    def have(self):
        return NumberValue(len(self.value), self.expect, format="len(%(value)r)")
    
    def be_close_to(self, value, delta=0.000001):
        self.expect(abs(self.value - value) < delta,
            "%(value)r %(should)s == %(other)r +/- %(delta)r",
            other=value, delta=delta)
            
    def change(self, obj, attr=None):
        chgVal = ChangeValue(obj, attr, self.expect)
        self.value()
        chgVal.capture_value_as_new()
        chgVal.expect_values_to_be_not_equal()
        return chgVal
        
    def instance_of(self, klass):
        self.expect(isinstance(self.value, klass),
            "%(value)r %(should)s be of class %(name)s instead of %(value_name)s",
            name=klass.__name__, value_name=type(self.value).__name__)
        
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
    #def __contains__(self, item):
    #    self.expect(item in self.value, "%(item)r %(should)s be in %(value)r", item=item)
    
    def __setitem__(self, key, value):
        raise Exception, "Value is unassignable. Did you mean ==?"
