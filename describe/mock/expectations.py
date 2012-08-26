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
    def __init__(self, attrname, returns=NO_ARG, args=ANYTHING, kwargs=ANYTHING):
        self.name, self.returns, self.args, self.kwargs = attrname, returns, args, kwargs

    @classmethod
    def raises(cls, attrname, error, args=ANYTHING, kwargs=ANYTHING):
        "An alternative constructor which raises the given error"
        def raise_error():
            raise error
        return cls(attrname, returns=Invoke(raise_error), args=ANYTHING, kwargs=ANYTHING)

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
        return '<Expect %(name)s(%(args)s) => %(returns)r>' % {
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

    def validate_expectation(self, expect, attrname, args, kwargs):
        if expect.satisfies_attrname(attrname):
            if expect.satisfies_arguments(args, kwargs):
                return self.process_expectation(expect, args, kwargs)
            else:
                raise self.FailedToSatisfyArgumentsError(expect)
        else:
            raise self.FailedToSatisfyAttrnameError(expect)

    def invoked(self, attrname, args, kwargs):
        try:
            if not self.expects:
                raise self.NoExpectationsError()
            return self.validate_expectation(self.expects[0], attrname, args, kwargs)
        except self.NoExpectationsError:
            return self.delegate.no_expectations(self, attrname, args, kwargs)
        except self.FailedToSatisfyAttrnameError as e:
            return self.delegate.fails_to_satisfy_attrname(self, attrname, args, kwargs, e.expect)
        except self.FailedToSatisfyArgumentsError as e:
            return self.delegate.fails_to_satisfy_arguments(self, attrname, args, kwargs, e.expect)

    def attribute_invoked(self, attrcatcher, args, kwargs):
        return self.invoked(attrcatcher._name_, args, kwargs)

    def attribute_read(self, attrcatcher, name):
        raise NotImplementedError("Invalid attr read")

    def key_read(self, attrcatcher, name):
        raise NotImplementedError("Invalid key access")

    def get_attribute(self, name):
        return self.invoked(name, (), {})

    def __len__(self):
        return len(self.expects)

    def __repr__(self):
        return "ExpectationList(expects=%r, history=%r)" % (self.expects, self.history)

class ExpectationSet(ExpectationList):
    """Contains an object-level unordered list of expectations.

    The mock can be invoked in any order.
    """
    def invoked(self, attrname, args, kwargs):
        for expect in self.expects:
            try:
                return self.validate_expectation(expect, attrname, args, kwargs)
            except (self.NoExpectationsError, self.FailedToSatisfyAttrnameError, self.FailedToSatisfyArgumentsError):
                pass
        return self.delegate.no_expectations(self, attrname, args, kwargs)

    def __repr__(self):
        return "ExpectationSet%r" % self.expects

class AttributeCatcher(object):
    "Simply captures values to pass to delegate."
    def __init__(self, name, delegate):
        self._name_, self._delegate_ = name, delegate

    def __call__(self, *args, **kwargs):
        return self._delegate_.attribute_invoked(self, args, kwargs)

    def __getitem__(self, key):
        return self._delegate_.key_read(self, key)

    def __getattribute__(self, name):
        if name in set(('__call__', '_delegate_', '_name_')):
            return super(AttributeCatcher, self).__getattribute__(name)
        return self._delegate_.attribute_read(self, name)


class ExpectationBuilder(object):
    """ExpectationBuilder handles the creation of Expectation objects.

    It attaches them to the given target
    """
    def __init__(self, delegate, add_invocations, add_expectations, attrname):
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
            self.add_invocations(self.attrname, value, self.args, self.kwargs)
        self.add_expectations(constructor(self.attrname, value, self.args, self.kwargs))

    def and_raise(self, error):
        self.__expect(Expectation.raises, error)

    def and_return(self, value):
        self.__expect(Expectation, value)

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
    def __init__(self, add_invocation, add_expectations, delegate):
        self.add_invocation = add_invocation
        self.add_expectations = add_expectations
        self.delegate = delegate

    def attribute_invoked(self, attrcatcher, args, kwargs):
        "Handles the creation of ExpectationBuilder when an attribute is invoked."
        return ExpectationBuilder(self.delegate, self.add_invocation, self.add_expectations, '__call__')(*args, **kwargs)

    def attribute_read(self, attrcatcher, name):
        "Handles the creation of ExpectationBuilder when an attribute is read."
        return ExpectationBuilder(self.delegate, self.add_invocation, self.add_expectations, name)

    def key_read(self, attrcatcher, name):
        "Handles the creation of ExpectationBuilder when a dictionary item access."
        return ExpectationBuilder(self.delegate, self.add_invocation, self.add_expectations, '__getitem__')(name)

