#    def __complex__(self):          return self.BuiltinTypeProcessor(self, complex)
#    def __int__(self):              return self.BuiltinTypeProcessor(self, int)
#    def __long__(self):             return self.BuiltinTypeProcessor(self, long)
#    def __float__(self):            return self.BuiltinTypeProcessor(self, float)
#    def __oct__(self):              return self.BuiltinTypeProcessor(self, oct)
#    def __hex__(self):              return self.BuiltinTypeProcessor(self, hex)

from values import *
from mixins import *

__all__ = ['SharedValue', 'IntegerValue', 'FloatValue', 'BuiltinTypesMixin']

class SharedValue(BuiltinFunctionsMixin, CollectionMixin, OperatorsMixin,
    PropertyMixin, StringMixin, EnumerableMixin, InvokerMixin, BaseValue):
    pass

class BaseTypeValue(SharedValue):
    TYPE = None
    def __init__(self, value):
        if isinstance(value, SharedValue):
            value = self.TYPE(value.value)
        super(BaseTypeValue, self).__init__(value)

UnicodeValue = None
class StrValue(BaseTypeValue, str):
    TYPE = str
    def __str__(self):
        return self
    
    def __unicode__(self):
        global UnicodeValue
        return UnicodeValue(self.value)
    
    def __oct__(self):
        return self._new_value(oct(self.value))
    
    def __hex__(self):
        return self._new_Value(hex(self.value))

class StrBuiltin(object):
    def __str__(self):
        return StrValue(self.value)
    
    def __oct__(self):
        return StrValue(oct(self.value))
    
    def __hex__(self):
        return StrValue(hex(self.value))

class UnicodeValue(StrBuiltin, BaseTypeValue, unicode):
    TYPE = unicode
    def __unicode__(self):
        return self

class UnicodeBuiltin(object):
    def __unicode__(self):
        return UnicodeValue(self.value)

class IntegerValue(BaseTypeValue, int):
    TYPE = int
    def __int__(self):
        return self
    
    def __float__(self):
        return self
    
    def __complex__(self):
        return self

class IntBuiltin(object):
    def __int__(self):
        return IntegerValue(self.value)

class LongValue(IntBuiltin, BaseTypeValue, long):
    TYPE = long
    def __long__(self):
        return self

class LongBuiltin(object):
    def __long__(self):
        return LongValue(self.value)

class FloatValue(IntBuiltin, LongBuiltin, BaseTypeValue, float):
    TYPE = float
    def __float__(self):
        return self

class FloatBuiltin(object):
    def __float__(self):
        return FloatValue(self.value) 

class BuiltinTypesMixin(IntBuiltin, FloatBuiltin, LongBuiltin, StrBuiltin, UnicodeBuiltin):
    pass
