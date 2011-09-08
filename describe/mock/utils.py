from ..frozen_dict import FrozenDict
from args_matcher import ArgList

class Function(tuple):
    def __init__(self, (name, args, kwargs, is_property)):
        super(Function, self).__init__((name, tuple(args), FrozenDict(kwargs), is_property))

    @property
    def name(self): return self[0]
    @property
    def args(self): return self[1]
    @property
    def kwargs(self): return self[2]
    @property
    def is_property(self): return self[3]

    def with_args(self, args, kwargs):
        return self.__class__(self.name, args, kwargs, self.is_property)

    @property
    def arglist(self):
        return ArgList(self.args, self.kwargs)

    def __str__(self):
        return "%(prop)s%(name)s(%(args)s%(comma)s%(kwargs)s)" % {
            'prop': 'property:' if self.is_property else '',
            'name': self.name,
            'comma': ', ' if len(self.args) > 0 and len(self.kwargs) > 0 else '',
            'args': ', '.join(map(repr, self.args)),
            'kwargs': ', '.join("%r=%r" % (k,v) for k,v in self.kwargs.iteritems()),
        }

class FunctionArgs(object):
    def __init__(self, reciever, attribute, name):
        self._reciever, self._attr, self._name = reciever, attribute, name

    def __transfer(self, args, kwargs, is_property=False):
        attr = getattr(self._reciever, self._attr, None)
        func = Function((self._name, args, kwargs, is_property))
        if callable(attr):
            attr(func)
        else:
            setattr(self._reciever, self._attr, func)
        return self._reciever

    def __getattr__(self, name):
        return getattr(self.__transfer((), {}, is_property=True), name)

    def __call__(self, *args, **kwargs):
        return self.__transfer(args, kwargs)


class FunctionName(object):
    def __init__(self, reciever, attribute='func'):
        self._reciever, self._attr = reciever, attribute

    def __getattr__(self, name):
        return FunctionArgs(self._reciever, self._attr, name)

    def __repr__(self):
        return "<FunctionName -> %(recvr)r.%(attr)s>" % {
            'recvr':self._reciever,
            'attr':self._attr
        }
