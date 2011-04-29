from properties import Properties
from decorators import VerifyDecorator, DeferredDecorator
from ..tracebacks import get_current_stack, get_stack
import re
try:
    set
except ValueError:
    from sets import Set as set

__ALL__ = ['OperatorsMixin', 'BuiltinFunctionsMixin', 'PropertyMixin', 'InvokerMixin', 'NotMixin',
    'EnumerableMixin']

class OperatorsMixin(object):
    """All operators return new lazy Value object after operating on the wrapped value object."""
    def __add__(self, other):       return self._new_value(lambda: self.value + other,  lazy=True)
    def __radd__(self, other):      return self._new_value(lambda: other + self.value,  lazy=True)
    def __iadd__(self, other):      self.value += other; return self
    def __sub__(self, other):       return self._new_value(lambda: self.value - other,  lazy=True)
    def __rsub__(self, other):       return self._new_value(lambda: other - self.value, lazy=True)
    def __isub__(self, other):      self.value -= other; return self
    def __mul__(self, other):       return self._new_value(lambda: self.value * other,  lazy=True)
    def __rmul__(self, other):      return self._new_value(lambda: other * self.value,  lazy=True)
    def __imul__(self, other):      self.value *= other; return self
    def __div__(self, other):       return self._new_value(lambda: self.value / other,  lazy=True)
    def __rdiv__(self, other):      return self._new_value(lambda: other / self.value,  lazy=True)
    def __idiv__(self, other):      self.value /= other; return self
    def __floordiv__(self, other):  return self._new_value(lambda: self.value // other, lazy=True)
    def __rfloordiv__(self, other): return self._new_value(lambda: other // self.value, lazy=True)
    def __ifloordiv__(self, other): self.value //= other; return self
    def __mod__(self, other):       return self._new_value(lambda: self.value % other,  lazy=True)
    def __rmod__(self, other):      return self._new_value(lambda: other % self.value,  lazy=True)
    def __imod__(self, other):      self.value %= other; return self
    def __pow__(self, other):       return self._new_value(lambda: self.value ** other, lazy=True)
    def __rpow__(self, other):      return self._new_value(lambda: other ** self.value, lazy=True)
    def __ipow__(self, other):      self.value **= other; return self
    def __lshift__(self, other):    return self._new_value(lambda: self.value << other, lazy=True)
    def __rlshift__(self, other):   return self._new_value(lambda: other << self.value, lazy=True)
    def __ilshift__(self, other):   self.value <<= other; return self
    def __rshift__(self, other):    return self._new_value(lambda: self.value >> other, lazy=True)
    def __rrshift__(self, other):   return self._new_value(lambda: other >> self.value, lazy=True)
    def __irshift__(self, other):   self.value >>= other; return self
    def __and__(self, other):       return self._new_value(lambda: self.value & other,  lazy=True)
    def __rand__(self, other):      return self._new_value(lambda: other & self.value,  lazy=True)
    def __iand__(self, other):      self.value &= other; return self
    def __xor__(self, other):       return self._new_value(lambda: self.value ^ other,  lazy=True)
    def __rxor__(self, other):      return self._new_value(lambda: other ^ self.value,  lazy=True)
    def __ixor__(self, other):      self.value ^= other; return self
    def __or__(self, other):        return self._new_value(lambda: self.value | other,  lazy=True)
    def __ror__(self, other):       return self._new_value(lambda: other | self.value,  lazy=True)
    def __ior__(self, other):       self.value |= other; return self
    def __neg__(self):              return self._new_value(lambda: -self.value,         lazy=True)
    def __pos__(self):              return self._new_value(lambda: +self.value,         lazy=True)
    def __invert__(self):           return self._new_value(lambda: ~self.value,         lazy=True)
    def __str__(self):              return str(self.value)
    def __unicode__(self):          return unicode(self.value)

    def contains(self, substring):
        self.expect(substring in self.value,
            "%(substr)r %(should)s be a substring of %(value)r",
            substr=substring)

class BuiltinFunctionsMixin(object):
    """All builtin hooks return a new lazy value object when possible.
    
    If cannot return a new object (due to constraints of the hook, they are actively eval'ed)
    """
    def __abs__(self):                    return self._new_value(lambda: abs(self.value),     lazy=True)
    def __complex__(self):                return self._new_value(lambda: complex(self.value), lazy=True)
    def __int__(self):                    return self._new_value(lambda: int(self.value),     lazy=True)
    def __long__(self):                   return self._new_value(lambda: long(self.value),    lazy=True)
    def __float__(self):                  return self._new_value(lambda: float(self.value),   lazy=True)
    def __oct__(self):                    return self._new_value(lambda: oct(self.value),     lazy=True)
    def __hex__(self):                    return self._new_value(lambda: hex(self.value),     lazy=True)
    def __index__(self):                  return self.value.__index__()
    def __coerce__(self, other):          return self.value.__coerce__(other)
    # TODO: figure out of wrapping these values are acceptable
    # or some value, based operation is acceptable
    def __enter__(self):                  return self.value.__enter__()
    def __exit__(self, type, val, trace): return self.value.__exit__(type, val, trace)
    
class StringMixin(object):
    """String specific methods."""
    def requires_string(self):
        prev_stack = get_current_stack()[1]
        self.requires(type(self.value) == str,
            "Value(%(value)r).%(method)s %(should)s be type str, but was type %(actual)s.",
            method=prev_stack.name, actual=type(self.value).__name__)
    
    def match(self, regex):
        "Performs a regular expression match expectation."
        self.requires_string()
        self.expect(re.search(regex, self.value),
            "%(regex)r.search(%(value)r) %(should)s return a match.",
            regex=regex)
            

class EnumerableMixin(object):
    """Enumerable specific methods."""
    def requires_enumerable(self):
        prev_stack = get_current_stack()[1]
        try:
            return
        except TypeError:
            self.requires(False,
                "Value(%(val)r).%(method)s %(should)s be enumerable, but wasn't (tried iter()).",
                method=prev_stack.name,
                val=self.value)
                
    def iter_as_values(self):
        self.requires_enumerable()
        return iter(map(self._new_value, self.value))
        
    def enumerable(self):
        "Asserts that the wrapped value can be enumerated using iter()."
        self.expect(iter(self.value),
            "iter(%(value)r) %(should)s be supported.")
            
    def have_equal_elements_to(self, other):
        self.requires_enumerable()
        self.expect(tuple(self.value) == tuple(other),
            "tuple(%(value)r) should have equal elements to tuple(%(other)r).",
            other=other)
        
    @classmethod
    def iterate(cls, enumerables):
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
        super(NotMixin, self).expect(not assertion, message, **kwargs)