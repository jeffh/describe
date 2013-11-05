from describe.mock.utils import TWO_OPS_FULL, ONE_OPS, NIL, get_args_str
from describe.mock.expectations import Invoke, AttributeCatcher, Expectation, ExpectationBuilderFactory, ExpectationList, ExpectationSet
from describe.mock.registry import Registry, RegistryError


__all__ = ['Mock', 'verify_mock']


class MockErrorDelegate(object):
    def no_expectations(self, expectations, sender, attrname, args, kwargs):
        raise AssertionError('This mock has no expectations')

    def fails_to_satisfy_attrname(self, expectations, sender, attrname, args, kwargs, expectation):
        raise AssertionError('This mock does not have expectations for attribute: %r' % attrname)

    def fails_to_satisfy_arguments(self, expectations, sender, attrname, args, kwargs, expectation):
        raise AssertionError('This mock does not have expectations for: %s(%s)' % (attrname, get_args_str(args, kwargs)))


IGNORE_LIST = set((
    '__expectations__', '__invocations__', '__items__', 'expects', '__getitem__',
    '__bases__', '__class__', '__name__', '__call__'
))

def process(expectations, invocations, sender, name):
    if name in invocations:
        return AttributeCatcher(sender, name, expectations)
    return expectations.get_attribute(sender, name)


MAGIC_METHODS = ['getitem', 'setitem', 'call']

class Mock(object):
    """Mocks are stricted cousins of Stub. Then raise AssertionErrors for any unexpected attribute accesses
    or method calls.

    Only pre-expected methods and attribute accesses are allowed, in the given order.

    name: String. What to name this mock (for repr). Defaults to 'Mock'.
    instance_of: Class. What class should this mock be an instance of. Allows isinstance calls to pass appropriately.
    ordered: Boolean. Should expectations on this object care about ordering?
    error_delegate: An object that handles mock error cases. The object should have 3 methods:
        - no_expectations(expectations, attrname, args, kwargs): When no expectations are available
          in expectations to satisfy the attribute request.
        - fails_to_satisfy_attrname(expectations, attrname, args, kwargs, expectation): When expectation
          in expectations fails to satisfy the given attrname (when ordering of expectations matter)
        - fails_to_satisfy_arguments(expectations, attrname, args, kwargs, expectation): When
          expectation in expectations fails to satisfy the given argument flags / filters.
        Each method above should return the value that the Mock should return.
        The error delegate is used for stubs to customize the current mock behavior.
    expectations: An object that holds all the expectations. It can either be pre-filled with expectations
        or support the API to add expectations. Using this argument will make the mock ignore the
        ordered and error_delegate arguments.

        Internally. Mock normally creates one of two classes:
            - ExpectationSet: (ordered=False) Stores expectations that are order-independant. The mock
              won't require methods to be called in a particular order.
            - ExpectationList (ordered=True) Stores expectations that are order-dependant. The makes
              the mock require methods to be called in a particular order.

        The default delegate simply raises assertion errors.
    """
    def __init__(self, name='Mock', instance_of=None, ordered=True, error_delegate=None, expectations=None):
        self.__name__ = name
        if instance_of:
            self.__class__ = type('InstancedMock', (instance_of, self.__class__), {})
        if expectations is not None:
            self.__expectations__ = expectations
        else:
            if not error_delegate:
                error_delegate = MockErrorDelegate()
            if ordered:
                self.__expectations__ = ExpectationList(delegate=error_delegate)
            else:
                self.__expectations__ = ExpectationSet(delegate=error_delegate)
        self.__invocations__ = set('__%s__' % m for m in MAGIC_METHODS)
        self.__properties__ = {}

        try:
            Registry.get_closest().add(self)
        except RegistryError:
            pass

    def __repr__(self):
        return '<%s(0x%x)>' % (self.__name__, id(self))

    @property
    def expects(self):
        def add_method(sender, name, value, args, kwargs):
            self.__invocations__.add(name)
        def add_expectation(*expectations):
            self.__expectations__.add(*expectations)
        return AttributeCatcher(self, None, ExpectationBuilderFactory(self, add_method, add_expectation, MockErrorDelegate()))

    def __getattr__(self, name):
        return process(self.__expectations__, self.__invocations__, self, name)

    #def __setattr__(self, name, value):
    #   if name in IGNORE_LIST:
    #       return super(Mock, self).__setattr__(name, value)
    #   process(self.__expectations__, self.__invocations__, '__setattr__')(name, value)

    def _create_magic(name):
        full_name = '__%s__' % name
        def getter(self):
            if self.__properties__.get(full_name, NIL) is NIL:
                return process(self.__expectations__, self.__invocations__, self, full_name)
            return self.__properties__.get(full_name)
        def setter(self, value):
            self.__properties__[full_name] = value
        return property(getter, setter)

    for op in TWO_OPS_FULL + ONE_OPS + MAGIC_METHODS:
        exec('__%s__ = _create_magic(%r)' % (op, op))


class MissingMockExpectationError(AssertionError):
    def __init__(self, mock):
        self.mock = mock
        self.missing_expectations = []
        expects = []
        for e in self.mock.__expectations__.expects:
            self.missing_expectations.append(e)
            expects.append('expects %(name)s(%(args)s) called (will return %(returns)r)' % {
                'name': e.name,
                'returns': e.returns,
                'args': e.args_str,
            })

        super(self.__class__, self).__init__('Mock %r has unfulfilled expectations: \n\t%s' % (
            self.mock, '\n\t'.join(expects)
        ))


def verify_mock(m):
    """Verifies that all mock expectations were called.
    """
    if m.__expectations__.is_fulfilled(m):
        raise MissingMockExpectationError(m)
