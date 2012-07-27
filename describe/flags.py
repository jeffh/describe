""" flags.py - Various constants that have special meaning in describe.

INIT   - Represents a matcher be instanciated for initialization purposes only
NO_ARG - Represents no argument. This is Noner than None.
"""
__all__ = (
    'NO_ARG', 'NO_ARGS', 'ANY_ARG', 'ANYTHING', 'ANY_ARGS', 'ANY_KWARGS', 'is_flag',
    'params_match',
)

class Flag(object):
    def __init__(self, name):
        self.name = name

    def __callable__(self):
        return self

    def __repr__(self):
        return 'flag(%s)' % self.name

INIT = Flag('INIT')
NO_ARG = Flag('NO_ARG')
NO_KWARGS = NO_ARGS = Flag('NO_ARGS')

# used for argument matching
ANY_ARG = Flag('ANY_ARG')
ANYTHING = Flag('ANYTHING')
ANY_ARGS = Flag('ANY_ARGS')
ANY_KWARGS = Flag('ANY_KWARGS')

class DynamicFlag(object):
    def __repr__(self):
        return getattr(self, 'name', self.__class__.__name__.lower())

    def validate(self, argument):
        raise NotImplemented()

class Subclasses(DynamicFlag):
    def __init__(self, cls):
        self.cls = cls

    def validate(self, argument):
        try:
            return issubclass(argument, self.cls)
        except TypeError:
            return False


class InstanceOf(DynamicFlag):
    def __init__(self, cls):
        self.cls = cls

    def validate(self, argument):
        return isinstance(argument, self.cls)

class Contains(DynamicFlag):
    def __init__(self, item):
        self.item = item

    def validate(self, argument):
        try:
            return self.item in list(argument)
        except TypeError:
            return False

class IncludesPairs(DynamicFlag):
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def validate(self, argument):
        for key, value in self.kwargs.items():
            try:
                if argument[key] != value:
                    return False
            except (IndexError, KeyError, TypeError):
                return False
        return True

class _Callable(DynamicFlag):
    def __call__(self):
        return self

    def validate(self, argument):
        return callable(argument)
Callable = _Callable()

class _AmountCompare(DynamicFlag):
    def __init__(self, size):
        self.size = size

    def validate(self, argument):
        try:
            return self.cmp(argument, self.size)
        except TypeError:
            return False

    def cmp(self, arg, value):
        raise NotImplemented()

class LengthOf(_AmountCompare):
    def cmp(self, arg, value):
        return len(arg) == self.size

class AtLeast(DynamicFlag):
    def cmp(self, arg, value):
        return arg < self.size

class AtLeastEqual(DynamicFlag):
    def cmp(self, arg, value):
        return arg <= self.size

class AtMost(DynamicFlag):
    def cmp(self, arg, value):
        return arg > self.size

class AtMostEqual(DynamicFlag):
    def cmp(self, arg, value):
        return arg >= self.size

def is_flag(value):
    try:
        return issubclass(value, Flag) or issubclass(value, DynamicFlag)
    except TypeError:
        return isinstance(value, Flag) or isinstance(value, DynamicFlag)

def __arg_is(arg, *flags):
    if arg in flags:
        return True
    try:
        tuple(arg)
    except TypeError:
        return False
    if tuple(arg) in set((f,) for f in flags):
        return True
    return False


def args_match(actual_args, expected_args):
    if __arg_is(expected_args, ANYTHING, ANY_ARGS):
        return True
    if __arg_is(expected_args, NO_ARG, NO_ARGS):
        return not list(actual_args)
    if len(actual_args) != len(expected_args):
        return False
    for aarg, earg in zip(actual_args, expected_args):
        assert earg not in (ANYTHING, ANY_ARGS, NO_ARG, NO_ARGS), 'expected_args cannot have a list containing any of the following: (ANYTHING, ANY_ARGS, NO_ARG, NO_ARGS)'
        if aarg == earg or earg is ANY_ARG:
            continue
        if isinstance(earg, DynamicFlag):
            if earg.validate(aarg):
                continue
        return False
    return True

def kwargs_match(actual_args, expected_args):
    if __arg_is(expected_args, ANYTHING, ANY_KWARGS):
        return True
    if __arg_is(expected_args, NO_ARG, NO_KWARGS):
        return not list(actual_args)
    if len(actual_args) != len(expected_args):
        return False
    for (akey, aarg), (ekey, earg) in zip(sorted(actual_args.items()), sorted(expected_args.items())):
        assert earg not in (ANYTHING, ANY_ARGS, NO_ARG, NO_ARGS), 'expected_args cannot have a list containing any of the following: (ANYTHING, ANY_ARGS, NO_ARG, NO_ARGS)'
        if akey != ekey:
            return False

        if aarg == earg or earg is ANY_ARG:
            continue
        if isinstance(earg, DynamicFlag):
            if earg.validate(aarg):
                continue
        return False
    return True

def params_match(actual_args, actual_kwargs, expected_args, expected_kwargs):
    if __arg_is(expected_args, ANYTHING, ANY_ARGS) or __arg_is(expected_kwargs, ANYTHING, ANY_KWARGS):
        return True
    return args_match(actual_args, expected_args) and kwargs_match(actual_kwargs, expected_kwargs)


