from describe.flags import (NO_ARG, ANYTHING, is_flag, params_match)
from describe.mock.utils import get_args_str

class Invoke(object):
    """A simple wrapper around a function that indicates the function should be invoked instead being
    treated as a value.
    """
    def __init__(self, fn):
        self.fn = fn

    def __call__(self):
        return self.fn()

    def __repr__(self):
        return '<Invoke: %r>' % self.fn

class Expectation(object):
    "Handles the expectation for a given invocation / access."
    def __init__(self, sender, attrname, returns=NO_ARG, args=ANYTHING, kwargs=ANYTHING):
        self.sender, self.name, self.returns, self.args, self.kwargs =\
                sender, attrname, returns, args, kwargs

    @classmethod
    def raises(cls, sender, attrname, error, args=ANYTHING, kwargs=ANYTHING):
        "An alternative constructor which raises the given error"
        def raise_error():
            raise error
        return cls(sender, attrname, returns=Invoke(raise_error), args=ANYTHING, kwargs=ANYTHING)

    def satisfies_sender(self, sender):
        return self.sender is None or self.sender is sender

    def satisfies_attrname(self, name):
        return self.name == name

    def satisfies_arguments(self, args, kwargs):
        return params_match(args, kwargs, self.args, self.kwargs)

    def return_value(self):
        if isinstance(self.returns, Invoke):
            return self.returns()
        return self.returns

    def is_consumed(self):
        return True

    @property
    def args_str(self):
        return get_args_str(self.args, self.kwargs)

    def __repr__(self):
        return '<Expect %(sender)s.%(name)s(%(args)s) => %(returns)r>' % {
            'sender': self.sender,
            'name': self.name,
            'returns': self.returns,
            'args': self.args_str,
        }

class ExpectationList(object):
    """Contains an object-level ordered list of expectations.

    The mock must be invoked in this given order.
    """
    class FailedToSatisfyArgumentsError(Exception):
        def __init__(self, expect):
            self.expect = expect
    class FailedToSatisfyAttrnameError(Exception):
        def __init__(self, expect):
            self.expect = expect
    class NoExpectationsError(Exception):
        pass

    def __init__(self, *expectations, **kwargs):
        self.expects = list(expectations)
        self.history = []
        self.delegate = kwargs.pop('delegate')

    def add(self, *expectations):
        self.expects.extend(expectations)

    def process_expectation(self, expect, args, kwargs):
        if expect not in self.history:
            self.history.append(expect)
        try:
            result = expect.return_value()
        finally:
            if expect.is_consumed():
                try:
                    self.expects.remove(expect)
                except ValueError:
                    pass
        return result

    def validate_expectation(self, expect, sender, attrname, args, kwargs):
        if not expect.satisfies_sender(sender):
            raise self.FailedToSatisfyArgumentsError(expect)
        if not expect.satisfies_attrname(attrname):
            raise self.FailedToSatisfyAttrnameError(expect)
        if not expect.satisfies_arguments(args, kwargs):
            raise self.FailedToSatisfyArgumentsError(expect)

        return self.process_expectation(expect, args, kwargs)

    def invoked(self, sender, attrname, args, kwargs):
        try:
            if not self.expects:
                raise self.NoExpectationsError()
            return self.validate_expectation(self.expects[0], sender, attrname, args, kwargs)
        except self.NoExpectationsError:
            return self.delegate.no_expectations(self, sender, attrname, args, kwargs)
        except self.FailedToSatisfyAttrnameError as e:
            return self.delegate.fails_to_satisfy_attrname(self, sender, attrname, args, kwargs, e.expect)
        except self.FailedToSatisfyArgumentsError as e:
            return self.delegate.fails_to_satisfy_arguments(self, sender, attrname, args, kwargs, e.expect)

    def attribute_invoked(self, sender, name, args, kwargs):
        return self.invoked(sender, name, args, kwargs)

    def attribute_read(self, sender, name):
        raise NotImplementedError("Invalid attr read")

    def key_read(self, sender, name):
        raise NotImplementedError("Invalid key access")

    def get_attribute(self, sender, name):
        return self.invoked(sender, name, (), {})

    def expects_for_mock(self, m):
        return [e for e in self.expects if e.satisfies_sender(m)]

    def is_fulfilled(self, mock):
        return len(self.expects_for_mock(mock))

    def __len__(self):
        return len(self.expects)

    def __iter__(self):
        return iter(self.expects)

    def __repr__(self):
        return "ExpectationList(expects=%r, history=%r)<0x%x>" % (self.expects, self.history, id(self))

class ExpectationSet(ExpectationList):
    """Contains an object-level unordered list of expectations.

    The mock can be invoked in any order.
    """
    def invoked(self, sender, attrname, args, kwargs):
        for expect in self.expects:
            try:
                return self.validate_expectation(expect, sender, attrname, args, kwargs)
            except (self.NoExpectationsError, self.FailedToSatisfyAttrnameError, self.FailedToSatisfyArgumentsError):
                pass
        return self.delegate.no_expectations(self, attrname, args, kwargs)

    def __repr__(self):
        return "ExpectationSet%r" % self.expects

class AttributeCatcher(object):
    "Simply captures values to pass to delegate."
    def __init__(self, sender, name, delegate):
        self._sender_, self._name_, self._delegate_ = sender, name, delegate

    def __call__(self, *args, **kwargs):
        return self._delegate_.attribute_invoked(self._sender_, self._name_, args, kwargs)

    def __getitem__(self, key):
        return self._delegate_.key_read(self._sender_, key)

    def __getattribute__(self, name):
        if name in set(('__call__', '_delegate_', '_name_', '_sender_')):
            return super(AttributeCatcher, self).__getattribute__(name)
        return self._delegate_.attribute_read(self._sender_, name)


class ExpectationBuilder(object):
    """ExpectationBuilder handles the creation of Expectation objects.

    It attaches them to the given target
    """
    def __init__(self, sender, delegate, add_invocations, add_expectations, attrname):
        self.sender = sender
        self.delegate = delegate
        self.add_invocations = add_invocations
        self.add_expectations = add_expectations
        self.attrname = attrname
        self.is_attr_read = True
        self.args = NO_ARG
        self.kwargs = NO_ARG

    def __call__(self, *args, **kwargs):
        if not self.is_attr_read:
            raise AssertionError("Cannot invoke multiple times!")
        self.is_attr_read = False
        self.args = args
        self.kwargs = kwargs
        return self

    def __expect(self, constructor, value):
        if not self.is_attr_read:
            self.add_invocations(self.sender, self.attrname, value, self.args, self.kwargs)
        self.add_expectations(constructor(self.sender, self.attrname, value, self.args, self.kwargs))

    def and_raises(self, *errors):
        "Expects an error or more to be raised from the given expectation."
        for error in errors:
            self.__expect(Expectation.raises, error)

    def and_returns(self, *values):
        "Expects a value or more to be raised from the given expectation."
        for value in values:
            self.__expect(Expectation, value)

    def and_calls(self, *funcs):
        """Expects the return value from one or more functions to be raised
        from the given expectation.
        """
        for fn in funcs:
            self.__expect(Expectation, Invoke(fn))

    def and_yields(self, *values):
        """Expects the return value of the expectation to be a generator of the
        given values
        """
        def generator():
            for value in values:
                yield value
        self.__expect(Expectation, Invoke(generator))

    def called(self):
        self.__expect(Expectation, None)


class ExpectationBuilderFactory(object):
    """ExpectationBuilderFactory handles the creation of ExpectationBuilder.

    This is used in conjunction with AttributeCatcher (as a delegate) to generate
    ExpectationBuilder with a nice expectation API:

       >>> m = Mock()
       >>> m.expects # returns AttributeCatcher with delegate = ExpectationBuilderFactory
       # AttributeCatcher defers to ExpectationBuilderFactory, which returns an ExpectationBuilder
       >>> m.expects.foo() # returns ExpectationBuilder instance

    Parameters:
     - add_invocation(attrname, value, args, kwargs) is a method indicates a given
            attribute is a method invocation.
     - add_expectations(*expectations) is a method which adds one or more expectations to a list.
     - delegate is the instance to handle deferred methods from Expectation objects.
    """
    def __init__(self, sender, add_invocation, add_expectations, delegate):
        self.sender = sender
        self.add_invocation = add_invocation
        self.add_expectations = add_expectations
        self.delegate = delegate

    def attribute_invoked(self, sender, name, args, kwargs):
        "Handles the creation of ExpectationBuilder when an attribute is invoked."
        return ExpectationBuilder(self.sender, self.delegate, self.add_invocation, self.add_expectations, '__call__')(*args, **kwargs)

    def attribute_read(self, sender, name):
        "Handles the creation of ExpectationBuilder when an attribute is read."
        return ExpectationBuilder(self.sender, self.delegate, self.add_invocation, self.add_expectations, name)

    def key_read(self, sender, name):
        "Handles the creation of ExpectationBuilder when a dictionary item access."
        return ExpectationBuilder(self.sender, self.delegate, self.add_invocation, self.add_expectations, '__getitem__')(name)

