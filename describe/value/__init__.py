"""
.. module:: value
    :synopsis: Contains the Value object, which is used for assertions.

Here contains :class:`~describe.value.NotValue` and
:class:`~describe.value.Value` implementations. Although both have the
same methods and properties, the :class:`~describe.value.Value` class is
the only publically instanciable one. :class:`~describe.value.NotValue`
may be instanciated from the :class:`~describe.value.Value` class.

.. moduleauthor:: Jeff Hui <contrib@jeffhui.net>

"""

from builtin_values import *

from mixins import NotMixin

__all__ = ['Value']

class NotValue(BuiltinTypesMixin, NotMixin, SharedValue):
    """Internal use, do not create on your own. A Value object that negates all expectations."""
    def _new_plain_value(self, val):
        # the ugly hack to return the original Value class defined below
        return globals()['Value'](val)
    
    def __int__(self):
        return IntegerValue(self.value)


# Public API
class Value(BuiltinTypesMixin, SharedValue):
    """Wraps an given value to allow readable expectations.

    The constructor simply accepts one argument.

    :param value: The value to wrap. This can be any type.
    :param lazy: **Used internally.** If set to True, assumes value to be callable that returns
        the true value (aka, lazy values).
    :type lazy: bool

    The Value object supports most kinds of operator hooks.

    """
    def __init__(self, value, lazy=False):
        # seems useless? Yes, we only want this method defined for docs
        super(Value, self).__init__(value, lazy=lazy)
    
    def __int__(self):
        return IntegerValue(self.value)

    @property
    def should_not(self):
        """This is identical to negating all subsequent expectations.
        (Returns a new :class:`NotValue` object).

        The following are both equal::

            Value(1).should != 1
            Value(1).should_not == 1

        But for other expectations, ``should_not`` is the only simple way to
        negate the operation::

            Value((1,2,3)).should_not.contain(5)

        Like in normal boolean logic, a double negation will return a `Value` object.

        :returns: :class:`NotValue` instance that wraps the same value.
        :aliases: and_should_not

        .. seealso:: :attr:`~describe.value.Value.should`

        """
        return NotValue(self.raw_value, self.is_lazy)
    and_should_not = should_not
