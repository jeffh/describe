from itertools import izip_longest

from describe.spec.utils import get_true_function
from describe import flags
from describe.mock.consumers import (ValueConsumer, ErrorConsumer, IteratorConsumer,
    FunctionConsumer, raises, returns, iterates)


class NoArgMatchError(Exception):
    "The error thrown when ArgMatcher fails to match a given set of arguments."
    pass


class ArgMatcher(object):
    "Given an arg filter set, it can determine if various kinds of arguments will match it."
    def __init__(self, args=None, kwargs=None):
        args = tuple(args or ())
        kwargs = dict(kwargs or {})
        self.set(args, kwargs)

    def __str__(self):
        return "<ArgMatcher(args=%r, kwargs=%r)>" % (self.args, self.kwargs)

    def set(self, args, kwargs):
        self.args = tuple(args or ())
        self.kwargs = dict(kwargs or {})

        assert flags.ANYTHING not in self.kwargs.values(), \
                "describe.flags.ANYTHING cannot not be in kwargs"
        assert flags.ANYTHING not in self.kwargs.keys(), \
                "describe.flags.ANYTHING cannot be in kwargs"
        assert flags.ANYTHING not in self.args or (
                (flags.ANYTHING,) == self.args and not self.kwargs), \
                "describe.flags.ANYTHING should be only thing in args and have no kwargs."

    def __repr__(self):
        return "ArgMatcher(%r, %r)" % (self.args, self.kwargs)

    def _remove_ANY_KWARGS(self, args):
        return tuple(a for a in args if a is not flags.ANY_KWARGS)

    def _any_arg_matches(self, args):
        NO_VALUE = object()
        sargs = self._remove_ANY_KWARGS(self.args)
        if len(sargs) != len(args):
            return False
        for filter_arg, arg in izip_longest(sargs, args, fillvalue=NO_VALUE):
            if (filter_arg != arg and filter_arg != flags.ANY_ARG) or sargs is NO_VALUE:
                return False
        return True

    def _any_kwarg_matches(self, kwargs):
        NO_VALUE = object()
        if len(self.kwargs) != len(kwargs):
            return False
        for filter_kwarg, kwarg in izip_longest(self.kwargs.items(), kwargs.items(), fillvalue=NO_VALUE):
            if (filter_kwarg != kwarg and filter_kwarg[1] != flags.ANY_ARG) or kwargs is NO_VALUE:
                return False
        return True

    def _anything_matches(self):
        return (flags.ANYTHING,) == self.args

    def _any_args_matches(self):
        return flags.ANY_ARGS in self.args

    def _any_kwargs_matches(self):
        return flags.ANY_KWARGS in self.args

    def matches_args(self, args=None):
        args = tuple(args or ())
        return self._anything_matches() or self._remove_ANY_KWARGS(self.args) == args or \
                self._any_arg_matches(args) or self._any_args_matches()

    def matches_kwargs(self, kwargs=None):
        kwargs = dict(kwargs or {})
        return self._anything_matches() or self.kwargs == kwargs or \
                self._any_kwarg_matches(kwargs) or self._any_kwargs_matches()

    def matches(self, args=None, kwargs=None):
        return self.matches_args(args) and self.matches_kwargs(kwargs)


class Counter(object):
    """Tracks the number of times a matcher matches an argument. Also stores mechanisms
    for validating the proper count.
    """
    def __init__(self, start=0):
        self.error_message = 'Assertion Failed'
        self.current = start
        self.goal = None

    def __repr__(self):
        return "Counter(%r, error_message=%r, self.goal=%r)" % (
            self.current, self.error_message, self.goal
        )

    def set(self, count):
        self.current = count
        return self

    def set_goal(self, fn, error_message=''):
        self.goal = fn
        self.error_message = error_message
        return self

    def increment(self):
        self.current += 1

    def verify(self):
        return not callable(self.goal) or self.goal(self.current)


class ArgsTable(object):
    "Maps ArgMatcher instances to associated functions to invoke."
    def __init__(self, default=None):
        self.default = default
        self.matchers = []

    def add(self, fn, args=(), kwargs=None):
        self.matchers.insert(0, (
            ArgMatcher(args, kwargs),
            fn,
            Counter()
        ))

    def set_callcount(self, func, count):
        for _, fn, counter in self.matchers:
            if func == fn:
                counter.set(count)

    def get(self, args, kwargs):
        for matcher, fn, counter in self.matchers:
            if matcher.matches(args, kwargs):
                return matcher, fn, counter
        return None, None, None

    def get_by_func(self, func):
        for matcher, fn, counter in self.matchers:
            if fn == func:
                return matcher, fn, counter
        return None, None, None

    def verify_call_counts(self):
        for matcher, _, counter in self.matchers:
            assert counter.verify(), counter.error_message % {'matcher': matcher}

    def verify(self):
        self.verify_call_counts()

    def __call__(self, *args, **kwargs):
        matcher, fn, counter = self.get(args, kwargs)
        if fn:
            counter.increment()
            return fn(*args, **kwargs)
        if callable(self.default):
            return self.default(*args, **kwargs)
        raise NoArgMatchError


class AttributeArgument(object):
    """API Interface. Similar to ExpectationBuilder, but accepts any attribute to apply
    method expectation.

    """
    def __init__(self, stub, attr_builder, item_builder, call_builder):
        self.__stub = stub
        self.__attr_builder = attr_builder
        self.__item_builder = item_builder
        self.__call_builder = call_builder

    def __getattr__(self, name):
        return self.__attr_builder(name)

    def __getitem__(self, key):
        return self.__item_builder(key)

    def __call__(self, *args, **kwargs):
        return self.__call_builder(args, kwargs)


class ExpectationBuilder(object):
    "API interface. Applies the developer's intend into what works for the stub's ArgMatchers."
    def __init__(self, stub, name=None):
        self.__stub = stub
        self.__name = name
        self.__callable = raises(NoArgMatchError)
        self.__type = None

    def __getitem__(self, key):
        return self.build_getitem(key)

    def __call__(self, *args, **kwargs):
        return self.build_call(args, kwargs)

    def build_getattr(self, name):
        return self.__class__(self._getobj(), name)

    def _getobj(self, name=None):
        name = name or self.__name
        if name is None:
            return self.__stub
        return getattr(self.__stub, name)

    def _getargtable(self, type=None):
        type = type or self.__type
        if type == 'getitem':
            return self._getobj()._getitem_argstable
        return self._getobj()._argstable

    def build_call(self, args, kwargs):
        self.__type = None
        self._getargtable().add(self.invoke, args, kwargs)
        self.at_least(1)
        return self

    def build_getitem(self, key):
        self.__type = 'getitem'
        self._getargtable().add(self.invoke, (key,), {})
        self.at_least(1)
        return self

    def invoke(self, *args, **kwargs):
        return self.__callable(*args, **kwargs)

    def __set_counter_goal(self, goalfn, error_message):
        matcher, fn, counter = self._getargtable().get_by_func(self.invoke)
        counter.set_goal(goalfn, error_message)
        return self

    def exactly(self, times):
        def equal(c): return c == times

        return self.__set_counter_goal(equal,
                '%(matcher)s expected to be called exactly ' + str(times) + ' times.')

    def at_least(self, times):
        def greater_than_or_equal(c): return c >= times

        return self.__set_counter_goal(greater_than_or_equal,
                '%(matcher)s expected to be called at least ' + str(times) + ' times.')

    def at_most(self, times):
        def less_than_or_equal(c): return c <= times

        return self.__set_counter_goal(less_than_or_equal,
                '%(matcher)s expected to be called at most ' + str(times) + ' times.')

    def __create_returner(self, consumer):
        self.__callable = consumer
        return self.__stub

    def and_returns(self, *values):
        return self.__create_returner(ValueConsumer(values))

    def and_yields(self, *values):
        return self.__create_returner(IteratorConsumer(values))

    def and_calls(self, *functions):
        return self.__create_returner(FunctionConsumer(functions))

    def and_raises(self, *errors):
        return self.__create_returner(ErrorConsumer(errors))


DO_NOT_RECORD = (
    'DO_NOT_RECORD', '_create_magic_method', 'with_class_attrs', 'with_attrs',
    '_Stub__record_access', '__name', '_Stub__collection', '_argstable', 'calls',
    '_getitem_argstable', 'access_history', 'expects', '_Stub__callstub',
    'verify_expectations', '_Stub__children', '_Stub__parent', '_Stub__parent_attr',
    '_Stub__parent_oldvalue', '_Stub__create_stub', '_Stub__name', 'getitems',
)


class Stub(object):
    def __init__(self, name='stub', parent=None, parent_attr=None, parent_old_value=None, argstable=None, getitem_argstable=None):
        # if you add an attribute, include it in DO_NOT_RECORD list
        self.__name = name
        self.__collection = {}
        self.__parent = parent
        self.__parent_attr = parent_attr
        self.__parent_oldvalue = parent_old_value
        self._argstable = argstable or ArgsTable()
        self._getitem_argstable = getitem_argstable or ArgsTable()
        self.__callstub = None
        self.__children = []
        self.calls = []
        self.getitems = []
        self.access_history = []

    def verify_expectations(self):
        self._getitem_argstable.verify()
        self._argstable.verify()
        for child_stub in self.__children:
            child_stub.verify_expectations()
        # clean up
        if self.__parent:
            setattr(self.__parent, self.__parent_attr, self.__parent_oldvalue)

    @classmethod
    def attr(cls, obj, attrname):
        name = getattr(obj, '__name__', None) or getattr(getattr(obj, '__class__', None), '__name__', None) or ''
        if name:
            name = name + '.' + attrname
        else:
            name = 'ChildStub'
        stub = cls(name, parent=obj, parent_attr=attrname, parent_old_value=getattr(obj, attrname))
        setattr(obj, attrname, stub)
        return stub

    def with_attrs(self, **properties):
        for name, value in properties.items():
            setattr(self, name, value)
        return self

    def with_class_attrs(self, **properties):
        self.__class__ = type(
            'StubChild',
            (self.__class__,),
            properties
        )
        return self

    def __record_access(self, name):
        self.access_history.append(name)

    def _create_magic_method(name):
        full_name = '__%s__' % name
        stub = {}
        def getter(self):
            self.__record_access(full_name)
            if full_name not in stub:
                stub[full_name] = self.__create_stub(full_name)
            return stub[full_name]
        getter.__name__ = full_name
        return property(getter)

    for op in 'or add sub mul floordiv divmod lshift rshift and xor div truediv pow mod'.split(' '):
        exec('__%s__ = _create_magic_method(%r)' % (op, op))
        exec('__%s__ = _create_magic_method(%r)' % ('r' + op, 'r' + op))
        exec('__%s__ = _create_magic_method(%r)' % ('i' + op, 'i' + op))

    for op in 'neg pos abs invert enter exit eq ne'.split(' '):
        exec('__%s__ = _create_magic_method(%r)' % (op, op))

    def __repr__(self):
        return "<Stub %s>" % (self.__name,)
    __str__ = __repr__

    def __unicode__(self):
        return unicode(str(self))

    def __len__(self):
        return 1

    def __iter__(self):
        return iter([self.__iter__])

    def __create_stub(self, name):
        if name[0] not in ('(', '['):
            name = '.' + name
        return self.__class__(self.__name + name)

    def __getitem__(self, key):
        self.getitems.append(key)
        try:
            return self._getitem_argstable(key)
        except NoArgMatchError:
            if key not in self.__collection:
                self.__collection[key] = getattr(self, '[%r]' % key)
            return self.__collection[key]

    def __setitem__(self, key, value):
        self.__collection[key] = value

    def __getattribute__(self, name):
        try:
            if name not in DO_NOT_RECORD:
                self.__record_access(name)
            return super(Stub, self).__getattribute__(name)
        except AttributeError:
            if name in DO_NOT_RECORD:
                raise
            s = self.__create_stub(name)
            self.__children.append(s)
            setattr(self, name, s)
            return s
        #return super(Stub, self).__getattribute__(name)
        #raise AttributeError('%r missing attribute %r' % (self, name))

    def __call__(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        try:
            return self._argstable(*args, **kwargs)
        except NoArgMatchError:
            if self.__callstub is None:
                self.__callstub = self.__create_stub('__call__')
            return self.__callstub

    @property
    def expects(self):
        builder = ExpectationBuilder(self)
        return AttributeArgument(
            self, builder.build_getattr, builder.build_getitem, builder.build_call)


