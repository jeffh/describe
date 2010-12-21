from values import *
from mixins import *

__ALL__ = ['Value']

class SharedValue(BuiltinFunctionsMixin, OperatorsMixin, PropertyMixin, StringMixin,
    InvokerMixin, BaseValue):
    pass

class NotValue(NotMixin, SharedValue):
    def _new_plain_value(self, val):
        return globals()['Value'](val)

# Public API
class Value(SharedValue):
    """Provides a wrapper to an given value. Allows for readable assertions.
    
    >>> num = Value(4)
    >>> num.should == 4
    >>> num.should != 5
    
    If the value was a float we would want a near-equal comparison:
    >>> Value(1.0).should.be_close(5) # delta=0.000001 by default
    >>> Value(1.0).should.be_close(5, delta=0.000001)
    """
    @property
    def should_not(self):
        return NotValue(self.raw_value, self.is_lazy)
    
