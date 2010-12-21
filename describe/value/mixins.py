from properties import Properties
from decorators import VerifyDecorator, DeferredDecorator
import re
try:
    set
except ValueError:
    from sets import Set as set

__ALL__ = ['OperatorsMixin', 'BuiltinFunctionsMixin',
    'PropertyMixin', 'InvokerMixin', 'NotMixin']

class OperatorsMixin(object):
    def __add__(self, other): return self._new_value(lambda: self.value + other, lazy=True)
    def __radd__(self, other): return self._new_value(lambda: other + self.value, lazy=True)
    def __iadd__(self, other): self.value += other; return self
    def __sub__(self, other): return self._new_value(lambda: self.value - other, lazy=True)
    def __rsub__(self, other): return self._new_value(lambda: other - self.value, lazy=True)
    def __isub__(self, other): self.value -= other; return self
    def __mul__(self, other): return self._new_value(lambda: self.value * other, lazy=True)
    def __rmul__(self, other): return self._new_value(lambda: other * self.value, lazy=True)
    def __imul__(self, other): self.value *= other; return self
    def __div__(self, other): return self._new_value(lambda: self.value / other, lazy=True)
    def __rdiv__(self, other): return self._new_value(lambda: other / self.value, lazy=True)
    def __idiv__(self, other): self.value /= other; return self
    def __floordiv__(self, other): return self._new_value(lambda: self.value // other, lazy=True)
    def __rfloordiv__(self, other): return self._new_value(lambda: other // self.value, lazy=True)
    def __ifloordiv__(self, other): self.value //= other; return self
    def __mod__(self, other): return self._new_value(lambda: self.value % other, lazy=True)
    def __rmod__(self, other): return self._new_value(lambda: other % self.value, lazy=True)
    def __imod__(self, other): self.value %= other; return self
    def __pow__(self, other): return self._new_value(lambda: self.value ** other, lazy=True)
    def __rpow__(self, other): return self._new_value(lambda: other ** self.value, lazy=True)
    def __ipow__(self, other): self.value **= other; return self
    def __lshift__(self, other): return self._new_value(lambda: self.value << other, lazy=True)
    def __rlshift__(self, other): return self._new_value(lambda: other << self.value, lazy=True)
    def __ilshift__(self, other): self.value <<= other; return self
    def __rshift__(self, other): return self._new_value(lambda: self.value >> other, lazy=True)
    def __rrshift__(self, other): return self._new_value(lambda: other >> self.value, lazy=True)
    def __irshift__(self, other): self.value >>= other; return self
    def __and__(self, other): return self._new_value(lambda: self.value & other, lazy=True)
    def __rand__(self, other): return self._new_value(lambda: other & self.value, lazy=True)
    def __iand__(self, other): self.value &= other; return self
    def __xor__(self, other): return self._new_value(lambda: self.value ^ other, lazy=True)
    def __rxor__(self, other): return self._new_value(lambda: other ^ self.value, lazy=True)
    def __ixor__(self, other): self.value ^= other; return self
    def __or__(self, other): return self._new_value(lambda: self.value | other, lazy=True)
    def __ror__(self, other): return self._new_value(lambda: other | self.value, lazy=True)
    def __ior__(self, other): self.value |= other; return self
    def __neg__(self): return self._new_value(lambda: -self.value, lazy=True)
    def __pos__(self): return self._new_value(lambda: +self.value, lazy=True)
    def __invert__(self): return self._new_value(lambda: ~self.value, lazy=True)

class BuiltinFunctionsMixin(object):
    def __abs__(self): return self._new_value(lambda: abs(self.value), lazy=True)
    def __complex__(self): return self._new_value(lambda: complex(self.value), lazy=True)
    def __int__(self): return self._new_value(lambda: int(self.value), lazy=True)
    def __long__(self): return self._new_value(lambda: long(self.value), lazy=True)
    def __float__(self): return self._new_value(lambda: float(self.value), lazy=True)
    def __oct__(self): return self._new_value(lambda: oct(self.value), lazy=True)
    def __hex__(self): return self._new_value(lambda: hex(self.value), lazy=True)
    def __index__(self): return self.value.__index__()
    def __coerce__(self, other): return self.value.__coerce__(other)
    def __enter__(self): return self.value.__enter__()
    def __exit__(self, type, val, trace): return self.value.__exit__(type, val, trace)
    
class StringMixin(object):
    """Comparisons with strings."""
    def match(self, regex):
        self.expect(re.search(regex, self.value),
            "%(regex)r.search(%(value)r) %(should)s return a match.",
            regex=regex)
        
class PropertyMixin(object):
    """Allows getting/setting methods of the wrapped object."""
    @property
    def invoke(self):
        return Properties(self.value, self._new_value)
    
    @property
    def get(self):
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
        if not self.is_lazy:
            raise TypeError, "No function specified."
        return self._new_value(self.value)
    
    def __call__(self, *args, **kwargs):
        if not callable(self.value):
            self.expect(False, "%(value)r should callable.", method=method_name)
        return self._new_value(DeferredDecorator(self.value, args, kwargs), lazy=True)
    
    def raise_error(self, exception_class, str_or_re=None):
        #self.expect(not (self.is_lazy or callable(self.value)),
        #    "%(value_name)r %(should)s be callable.")
        try:
            return_value = self.value # lazy eval
            self.expect(False, "Calling %(value_name)r %(should)s throw %(exception)r",
                exception=exception_class.__name__)
            return VerifyDecorator(None)
        except AssertionError:
            raise
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
    """Like BaseValue, but is inverse NOT operations"""
    @property
    def should_not(self):
        return self._new_plain_value(self.__value)
        
    def change(self, obj, attr):
        chgVal = ChangeValue(obj, attr, self.expect)
        self.value()
        chgVal.capture_value_as_new()
        chgVal.expect_values_to_be_equal()
        return None # if we can't change value, we can't change by a specified amount.
        
    def expect(self, assertion, message=None, **kwargs):    
        if 'should' not in kwargs:
            kwargs['should'] = 'should not'
        super(NotMixin, self).expect(not assertion, message, **kwargs)