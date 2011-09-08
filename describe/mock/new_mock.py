import repository as repos
import mock as mocker
from ..value import Value
from ..mixins import InplaceOperatorsMixin, OperatorsMixin, ReverseOperatorsMixin, \
    LogicalOperatorsMixin, SequenceMixin
from utils import FunctionName, Function
from args_matcher import ArgList
from ..frozen_dict import FrozenDict
import operator

class ExpectationDelegator(object):
    def __init__(self):
        self._expects = []

    def register(self, expectation):
        self._expects.append(expectation)

    def reset(self):
        self._expects = []

    def __call__(self, *args, **kwargs):
        al = ArgList(args, kwargs)
        for el in self._expects:
            if el.can_handle_arglist(al):
                return el(*args, **kwargs)

def operator_any(a, b):
    return True

class AttributeExpectation(object):
    def __init__(self, mock, order_group, expected_access_count=1):
        self._mock = mock
        self._order_group = order_group
        self._actual_access_count = 0
        self._expected_access_count = expected_access_count
        self._validators = []
        self._values_to_yield = []
        self._args_recieved = []
        self._values_yielded = []
        self._funcdef = None # this will get set shortly after construction
        self._current_access_count_expectation = None
        self._called_max_times = lambda: False
        # enforce that an expectation expects at least being called once
        self.at_least('once') # mutable operations

    def can_handle_arglist(self, arglist):
        """This is used internally, you may or may not use this.

        Returns True if this expectation object can handle/process the given arglist.
        """
        return self._funcdef.arglist == arglist and not self._called_max_times()

    def set_funcdef(self, value):
        """Internal use. Do not call manually.

        This is called by the FunctionName (really FunctionArgs object) which gives us a Function
        object.
        """
        self._funcdef = value
        delegator = getattr(self._mock.mock, self._funcdef.name, None) # mock will already return something
        # here is where the magic occurs: we assign the given attribute of the mock to a Delegator
        # and register ourselves to it.
        if delegator is None or getattr(delegator, 'call_count', None) == 0:
            delegator = ExpectationDelegator()
            setattr(self._mock.mock, self._funcdef.name, delegator)
            self._mock.mock.side_effect = delegator
            self._mock._reset_hook.append(delegator.reset)
        delegator.register(self)
        if self._funcdef.is_property:
            self.as_property

    def _verify_consumed_all(self):
        """Verification function to check if all values were consumed."""
        message = "Not all specified return values were used."
        assert len(self._values_to_yield) == 0, message

    def and_return(self, value, *values):
        """Sets the return value that this expectation should return"""
        self.and_return_from_callable(lambda *a, **kw: value)
        for v in values:
            def scope(value_to_return):
                def f(*args, **kwargs):
                    return value_to_return
                return f
            self.and_return_from_callable(scope(v))
        return self

    def and_raise(self, error, message=None):
        """Sets the exception to throw when this expectation occurs."""
        def throw(*args, **kwargs):
            if message:
                raise error, message
            else:
                raise error
        return self.and_return_from_callable(throw)
    and_throw = and_throw_error = and_raise_error = and_raise

    OPERATOR_INFO = {
        # operator function: (human-friendly name, called max times func)
        operator.le: 'at least',
        operator.ge: 'at most',
        operator.eq: 'exactly',
        operator.lt: 'at least greater than',
        operator.ge: 'at most less than',
        operator_any: '',
    }
    NUMERIC_MAP = {
        'none': 0,
        'nothing': 0,
        'never': 0,
        'zero': 0,
        'once': 1,
        'one': 1,
        'twice': 2,
        'two': 2,
        'thrice': 3,
        'three': 3,
        'four': 4,
        'five': 5,
        'six': 6,
        'seven': 7,
        'eight': 8,
        'nine': 9,
    }

    def _called_max_times(self):
        return self._expected_access_count and self._expected_access_count <= self._actual_access_count

    def _set_count_expectation(self, op, value):
        if self._current_access_count_expectation:
            self._validators.remove(self._current_access_count_expectation)
        self._expected_access_count = self.NUMERIC_MAP.get(value, False) or int(value)
        def func():
            message = "%(name)r was accessed %(a)r time%(as)s when expected %(op)s %(e)r time%(es)s." % {
                'name': self._funcdef.name,
                'op': self.OPERATOR_INFO[op],
                'as': 's' if self._actual_access_count != 1 else '',
                'a': self._actual_access_count,
                'es': 's' if self._expected_access_count != 1 else '',
                'e': self._expected_access_count,
            }
            assert op(self._expected_access_count, self._actual_access_count), message
        self._current_access_count_expectation = func
        self._validators.append(self._current_access_count_expectation)
        return self

    def at_least(self, n):
        return self._set_count_expectation(operator.le, n)

    def at_most(self, n):
        return self._set_count_expectation(operator.ge, n)

    @property
    def any_number_of_times(self):
        return self._set_count_expectation(operator_any, 0)

    def exactly(self, n):
        return self._set_count_expectation(operator.eq, n)

    @property
    def once(self):
        return self.exactly(1)
    one = once
    @property
    def twice(self):
        return self.exactly(2)
    two = twice
    @property
    def never(self):
        return self.exactly(0)
    zero = never
    @property
    def times(self):
        return self
    time = times

    def and_return_from_callable(self, func, *funcs):
        assert callable(func), "Given object (%r) isn't callable." % func
        assert len(funcs) == 0 or any(map(callable, funcs)), "Not all objects in (%r) is callable" % funcs
        self._values_to_yield.append(func)
        self._values_to_yield.extend(funcs)
        return self

    def _consume_return_value(self, *args, **kwargs):
        self._order_group.verify_position(self)
        try:
            self._values_yielded.append(self._values_to_yield[0])
            return self._values_to_yield.pop(0)(*args, **kwargs)
        except IndexError:
            #self._values_to_yield.append()
            try:
                return self._values_to_yield[-1](*args, **kwargs)
            except IndexError:
                return None

    def verify(self):
        for v in self._validators:
            v()

    def __call__(self, *args, **kwargs):
        self._actual_access_count += 1
        self._args_recieved.append(ArgList(args, kwargs))
        return self._consume_return_value(*args, **kwargs)

    def __repr__(self):
        return str(self._funcdef)

    @property
    def as_property(self):
        # TODO: inject some property handling methods to work accross multiple mock objects
        setattr(self._mock.__class__, self._funcdef.name, property(lambda s: self()))
        return self

    @property
    def ordered(self):
        self._order_group.append(self)

class OrderingGroup(object):
    def __init__(self, raise_immediately=False):
        self.raise_immediately = raise_immediately
        # the max element that was correct
        self.correct_index = 0
        self._objs = []
        self._first_error = None

    def append(self, obj):
        self._objs.append(obj)

    def index(self, index, start=None):
        return self._objs.index(index, start)

    def __getitem__(self, index):
        return self._objs[index]

    def __len__(self):
        return len(self._objs)

    def verify(self):
        error, self._first_error = self._first_error, None
        if error:
            raise error

    def reset(self):
        self._objs = []

    def verify_position(self, expectation):
        if len(self) == 0:
            return True
        try:
            i = self.index(expectation, self.correct_index)
        except ValueError:
            return True
        j = self.correct_index
        self.correct_index = i + 1
        if i != j:
            message = "%(actual)r was accessed, but expected %(actual)r to be accessed after %(expected)r (%(index)d attribute access%(es)s later)." % {
                'actual': expectation,
                'expected': self[0],
                'index': i,
                'es': 'es' if i != 1 else '',
            }
            if self.raise_immediately:
                raise AssertionError, message
            else:
                self._first_error = AssertionError(message)
            return False
        return True

class Mock(InplaceOperatorsMixin, OperatorsMixin, ReverseOperatorsMixin, LogicalOperatorsMixin, SequenceMixin):
    def __init__(self, klass=None, repository=repos.default, strict=True, mock_class=mocker.Mock):
        if repository:
            repository.register(self)
        self.mock = mock_class(spec=klass)
        self._strict = strict
        self._order_group = OrderingGroup()
        self._validators = [self._order_group.verify]
        self._exclude_list = []
        self._access_log = []
        self._reset_hook = []

    # === override the default processors for the mixins to pass the work to the mock object.
    # For whatever reason, __getattr__() doesn't pick these hooks up.
    def _operator_to_mock(self, a, b, op, single_arg=False):
        if single_arg:
            return op(a.mock)
        return op(a.mock, b)
    LogicalOperatorProcessor = OperatorProcessor = ReverseOperatorProcessor = _operator_to_mock

    def _inplace_operator_to_mock(self, a, b, op):
        a.mock = op(a.mock, b)
        return a
    InplaceOperatorProcessor = _inplace_operator_to_mock

    def _seq_processor(self, a, args, op):
        return op(a.mock, *args)
    SequenceProcessor = _seq_processor

    # === end overrides

    @property
    def should_access(self):
        ma = AttributeExpectation(self, self._order_group)#MockAttribute(self)
        self._validators.append(ma.verify)
        return FunctionName(ma, attribute='set_funcdef')

    @property
    def should_not_access(self):
        return FunctionName(self, attribute='_add_function_to_not_access')

    def _add_function_to_not_access(self, func):
        self._exclude_list.append(func.name)

    def verify(self, strict=True):
        try:
            for v in self._validators:
                v()
            if strict and self._strict:
                exclude = set(self._exclude_list)
                for attr in self._access_log:
                    if attr in exclude:
                        msg = "Mock expected that %(name)r would not be accessed." % {'name': attr}
                        raise AssertionError, msg
        finally:
            self.reset_mock()

    def reset_mock(self):
        for r in self._reset_hook:
            r()
        self._reset_hook = []
        self._access_log = []
        self._order_group.reset()
        self.mock.reset_mock()

    def __getattr__(self, name):
        self._access_log.append(name)
        return getattr(self.mock, name)

