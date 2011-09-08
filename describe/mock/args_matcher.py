from args_filter import *
from args_filter import MISSING_ARG
import itertools
from ..frozen_dict import FrozenDict

def arg_equal(arg1, arg2):
    if type(arg1) == type(arg2) == ArgFilter:
        return arg1 == arg2 or arg1.verify(arg2) or arg2.verify(arg1)
    elif type(arg1) == ArgFilter:
        return arg1.verify(arg2)
    elif type(arg2) == ArgFilter:
        return arg2.verify(arg1)
    return arg1 == arg2


class ArgList(object):
    def __init__(self, args=(), kwargs=None):
        if kwargs is None:
            kwargs = {}
        self.args, self.kwargs = tuple(args), FrozenDict(kwargs)

    def __repr__(self):
        return "ArgList(%r, %r)" % (self.args, self.kwargs)

    def __str__(self):
        return "ArgList(%(args)s%(comma)s%(kwargs)s)" % {
            'comma': ', ' if len(self.args) > 0 and len(self.kwargs) > 0 else '',
            'args': ', '.join(map(str, self.args)),
            'kwargs': ', '.join("%s=%s" % (k,v) for k,v in self.kwargs.iteritems()),
        }

    def __hash__(self):
        return hash((self.args, self.kwargs))

    def __iter__(self):
        return iter((self.args, self.kwargs))

    @property
    def is_anything(self):
        return ANYTHING in self.args

    def __eq__(self, other):
        if self.is_anything or other.is_anything:
            return True

        matches_any_kwargs = False
        culmulated_ANY_ARGs1 = culmulated_ANY_ARGs2 = 0
        other_args = other.args
        for arg1, arg2 in itertools.izip_longest(self.args, other_args, fillvalue=MISSING_ARG):
            if arg1 == KWARGS or arg2 == KWARGS:
                matches_any_kwargs = True
                self.args = tuple(x for x in self.args if x != KWARGS)
                other_args = tuple(x for x in other.args if x != KWARGS)

        for arg1, arg2 in itertools.izip_longest(self.args, other_args, fillvalue=MISSING_ARG):
            if arg1 == ARGS or arg2 == ARGS:
                break # check kwargs
            if not arg_equal(arg1, arg2):
                return False

        for arg1, arg2 in itertools.izip_longest(self.kwargs.values(), other.kwargs.values(), fillvalue=MISSING_ARG):
            if arg1 == KWARGS or arg2 == KWARGS:
                matches_any_kwargs = True
                break

        if matches_any_kwargs:
            return True

        keys_compared = []
        for key, val in self.kwargs.iteritems():
            keys_compared.append(key)
            if key not in other.kwargs or not arg_equal(val, other.kwargs[key]):
                return False

        keys_compared = set(keys_compared)
        for key, val in other.kwargs.iteritems():
            if key in keys_compared:
                continue
            if key not in self.kwargs or not arg_equal(val, self.kwargs[key]):
                return False

        return True
