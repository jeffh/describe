""" flags.py - Various constants that have special meaning in describe.

INIT   - Represents a matcher be instanciated for initialization purposes only
NO_ARG - Represents no argument. This is Noner than None.
"""
__all__ = (
    'ANY_ARG', 'ANYTHING', 'ANY_ARGS', 'ANY_KWARGS', 'is_flag',
)

class _Flag(object):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return 'flag(%s)' % self.name

INIT = _Flag('INIT')
NO_ARG = _Flag('NO_ARG')

# used for argument matching
ANY_ARG = _Flag('ANY_ARG')
ANYTHING = _Flag('ANYTHING')
ANY_ARGS = _Flag('ANY_ARGS')
ANY_KWARGS = _Flag('ANY_KWARGS')


# dynamic flag matching
class _FlagWithData(_Flag):
    def __init__(self, name, args, kwargs):
        super(_FlagWithData, self).__init__(name)
        self.args, self.kwargs = args, kwargs

class _FlagGenerator(_Flag):
    def __init__(self, name, accepts_args=True, accepts_kwargs=True):
        self.name = name
        self.accepts_args = accepts_args
        self.accepts_kwargs = accepts_kwargs

    def __repr__(self):
        return "flagGenerator(%s)" % self.name

    def __call__(self, *args, **kwargs):
        assert self.accepts_args or not args, "Args cannot be defined."
        assert self.accepts_kwargs or not kwargs, "Kwargs cannot be defined."
        return _FlagWithData(namem, args, kwargs)

# TODO: implement these in ArgMatcher class
SUBCLASS = _FlagGenerator('SUBCLASS')
INSTANCE = _FlagGenerator('INSTANCE')
CONTAINS = _FlagGenerator('CONTAINS')
INCLUDES_PAIRS = _FlagGenerator('INCLUDES_PAIRS')
CALLABLE = _FlagGenerator('CALLABLE')
LEN = _FlagGenerator('LEN')


def is_flag(value):
    return value in (INIT, NO_ARG, ANY_ARG, ANYTHING, ANY_ARGS, ANY_KWARGS)
