import operator

def default_operator_processor(a, b, operatorfn, single_arg=False):
    raise NotImplemented
    if single_arg:
        return operatorfn(a)
    return operatorfn(a, b)

def default_sequences_processor(obj, args, operatorfn):
    return operatorfn(obj, *args)

def default_builtin_processor(obj, typefn):
    return typefn(obj)

div = operator.div
idiv = operator.idiv
if 1/2 == 0.5: # true div
    div = operator.truediv
    idiv = operator.itruediv

class InplaceOperatorsMixin(object):
    """Provides an abstraction to manually overriding all inplace operator methods."""
    InplaceOperatorProcessor = default_operator_processor

    def __iadd__(self, other):      return self.InplaceOperatorProcessor(self, other, operator.iadd)
    def __isub__(self, other):      return self.InplaceOperatorProcessor(self, other, operator.isub)
    def __imul__(self, other):      return self.InplaceOperatorProcessor(self, other, operator.imul)
    def __idiv__(self, other):      return self.InplaceOperatorProcessor(self, other, idiv)
    def __ifloordiv__(self, other): return self.InplaceOperatorProcessor(self, other, operator.ifloordiv)
    def __imod__(self, other):      return self.InplaceOperatorProcessor(self, other, operator.imod)
    def __ipow__(self, other):      return self.InplaceOperatorProcessor(self, other, operator.ipow)
    def __ilshift__(self, other):   return self.InplaceOperatorProcessor(self, other, operator.ilshift)
    def __irshift__(self, other):   return self.InplaceOperatorProcessor(self, other, operator.irshift)
    def __iand__(self, other):      return self.InplaceOperatorProcessor(self, other, operator.iand)
    def __ixor__(self, other):      return self.InplaceOperatorProcessor(self, other, operator.ixor)
    def __ior__(self, other):       return self.InplaceOperatorProcessor(self, other, operator.ior)

class ReverseOperatorsMixin(object):
    """All operators return new lazy Value object after operating on the wrapped value object."""
    ReverseOperatorProcessor = default_operator_processor

    def __radd__(self, other):      return self.ReverseOperatorProcessor(other, self, operator.radd)
    def __rsub__(self, other):      return self.ReverseOperatorProcessor(other, self, operator.sub)
    def __rmul__(self, other):      return self.ReverseOperatorProcessor(other, self, operator.mul)
    def __rdiv__(self, other):      return self.ReverseOperatorProcessor(other, self, div)
    def __rfloordiv__(self, other): return self.ReverseOperatorProcessor(other, self, operator.floordiv)
    def __rmod__(self, other):      return self.ReverseOperatorProcessor(other, self, operator.mod)
    def __rpow__(self, other):      return self.ReverseOperatorProcessor(other, self, operator.rpow)
    def __rlshift__(self, other):   return self.ReverseOperatorProcessor(other, self, operator.lshift)
    def __rrshift__(self, other):   return self.ReverseOperatorProcessor(other, self, operator.rshift)
    def __rand__(self, other):      return self.ReverseOperatorProcessor(other, self, operator.and_)
    def __rxor__(self, other):      return self.ReverseOperatorProcessor(other, self, operator.xor)
    def __ror__(self, other):       return self.ReverseOperatorProcessor(other, self, operator.or_)

class OperatorsMixin(object):
    """All operators return new lazy Value object after operating on the wrapped value object."""
    OperatorProcessor = default_operator_processor

    def __add__(self, other):       return self.OperatorProcessor(self, other, operator.add)
    def __sub__(self, other):       return self.OperatorProcessor(self, other, operator.sub)
    def __mul__(self, other):       return self.OperatorProcessor(self, other, operator.mul)
    def __div__(self, other):       return self.OperatorProcessor(self, other, div)
    def __floordiv__(self, other):  return self.OperatorProcessor(self, other, operator.floordiv)
    def __mod__(self, other):       return self.OperatorProcessor(self, other, operator.mod)
    def __pow__(self, other):       return self.OperatorProcessor(self, other, operator.pow)
    def __lshift__(self, other):    return self.OperatorProcessor(self, other, operator.lshift)
    def __rshift__(self, other):    return self.OperatorProcessor(self, other, operator.rshift)
    def __and__(self, other):       return self.OperatorProcessor(self, other, operator.and_)
    def __xor__(self, other):       return self.OperatorProcessor(self, other, operator.xor)
    def __or__(self, other):        return self.OperatorProcessor(self, other, operator.or_)
    def __neg__(self):              return self.OperatorProcessor(self, None, operator.neg, single_arg=True)
    def __pos__(self):              return self.OperatorProcessor(self, None, operator.pos, single_arg=True)
    def __invert__(self):           return self.OperatorProcessor(self, None, operator.invert, single_arg=True)

class LogicalOperatorsMixin(object):
    """All hooks that are used for logical operations."""
    LogicalOperatorProcessor = default_operator_processor

    def __nonzero__(self):          return self.LogicalOperatorProcessor(self, None, operator.truth, single_arg=True)
    def __lt__(self, other):        return self.LogicalOperatorProcessor(self, other, operator.lt)
    def __le__(self, other):        return self.LogicalOperatorProcessor(self, other, operator.le)
    def __eq__(self, other):        return self.LogicalOperatorProcessor(self, other, operator.eq)
    def __ne__(self, other):        return self.LogicalOperatorProcessor(self, other, operator.ne)
    def __ge__(self, other):        return self.LogicalOperatorProcessor(self, other, operator.ge)
    def __gt__(self, other):        return self.LogicalOperatorProcessor(self, other, operator.gt)

class BuiltinFunctionsMixin(object):
    """All hooks that coerce the object to a given type, but not strictly enforced."""
    BuiltinFunctionProcessor = default_builtin_processor

    def __abs__(self):              return self.BuiltinFunctionProcessor(self, abs)

class BuiltinTypesMixin(object):
    BuiltinTypeProcessor = default_builtin_processor

    def __oct__(self):              return self.BuiltinTypeProcessor(self, oct)
    def __hex__(self):              return self.BuiltinTypeProcessor(self, hex)

class SequenceMixin(object):
    """All hooks that deal with collection of items."""
    SequenceProcessor = default_sequences_processor

    def __contains__(self, obj):    return self.SequenceProcessor(self, (obj,), operator.contains)
    def __getitem__(self, obj):     return self.SequenceProcessor(self, (obj,), operator.getitem)
    def __setitem__(self, obj, val):return self.SequenceProcessor(self, (obj,val), operator.setitem)
    def __delitem__(self, obj):     return self.SequenceProcessor(self, (obj,), operator.delitem)

