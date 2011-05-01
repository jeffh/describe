import repository as repos
import mock as mocker
from .. import Value, mixins
from utils import FunctionName, Function
from args_matcher import ArgList
from ..frozen_dict import FrozenDict

class MockAttribute(object):
    def __init__(self, mock):
        self.mock = mock
        self._validators = [self._verify_allreturns]
        self._funcdef = None
        self._return_list = {}
        self._extra_args_recieved = []
        
    def __repr__(self):
        return "<MockAttribute:0x%(id)x, %(funcdef)r, %(return)r on %(mock)r>" % {
            'id': id(self),
            'funcdef': self._funcdef,
            'return': self._return_list,
            'mock': self.mock,
        }
        
    def funcdef(self, value):
        self._funcdef = value
        setattr(self.mock.mock, self._funcdef.name, self)
        if self._funcdef.is_property:
            self.as_property
        key = self._freeze(self._funcdef.args, self._funcdef.kwargs)
        if key not in self._return_list:
            self._return_list[key] = []
        self._return_list[key].append(None)
        
    def verify(self):
        for v in self._validators:
            v()
        
    def _freeze(self, args, kwargs):
        """Converts args and kwargs into a hashed, immutable data struct."""
        return ArgList(tuple(args), FrozenDict(kwargs))
        
    def __call__(self, *args, **kwargs):
        # special case with __hooks__: replace self.mock.mock with self.mock
        if self._funcdef.name.startswith('__') and self._funcdef.name.endswith('__'):
            if args[0] == self.mock.mock:
                args = (self.mock,) + args[1:]
        al = self._freeze(args, kwargs)
        try:
            result = self._return_list[al].pop()
        except KeyError:
            # without creating a complex hashing algorithm, we'll have to check all argument lists
            # manually. This shouldn't be too bad since the size of this dict is probably pretty small
            has_result = False
            for arglist, r in self._return_list.iteritems():
                if arglist == al:
                    result = r
                    self._return_list[arglist].pop()
                    has_result = True
                    break
            if not has_result:
                self._extra_args_recieved.append((args, kwargs))
                return None
        if callable(result):
            return result(*args, **kwargs)
        return result
        
    def _verify_allreturns(self):
        for key,value in self._return_list.iteritems():
            msg = "'%(func)s' was expected, but didn't happen." % {
                'func': str(Function((self._funcdef.name,) + tuple(key) + (self._funcdef.is_property,))),
            }
            assert len(value) == 0, msg
        
    def exactly(self, n):
        def validate():
            assert self.mock.call_count == n, \
                "%(name)s was called %(c)d times when it was expected to only be called %(n)d times" % {
                    'name': self._funcdef.name,
                    'c': self.mock.call_count,
                    'n': n,
                }
        self._validators.append(validate)
        return self
        
    @property
    def times(self):
        pass
    
    def and_raise(self, exception):
        def throw(*args, **kwargs):
            raise exception
        return self.and_return(throw)
        
    def and_return(self, value):
        key = self._freeze(self._funcdef.args, self._funcdef.kwargs)
        self._return_list[key][-1] = value
        return self
    
    @property
    def as_property(self):
        # TODO: inject some property handling methods to work accross multiple mock objects
        setattr(self.mock.__class__, self._funcdef.name, property(lambda s: self()))
        return self

class Mock(mixins.InplaceOperatorsMixin, mixins.OperatorsMixin, mixins.ReverseOperatorsMixin, mixins.LogicalOperatorsMixin, mixins.SequenceMixin):
    def __init__(self, klass=None, repository=repos.default, strict=True):
        if repository:
            repository.register(self)
        if klass is not None:
            self.mock = mocker.MagicMock(spec=klass)
        else:
            self.mock = mocker.Mock()
        self._strict = strict
        self._validators = [self._order_group.verify]
        self._exclude_list = []
        self._access_log = []
        
    # === override the default processors for the mixins to pass the work to the mock object.
    # For some strange reason, __getattr__() doesn't pick these hooks up.
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
        ma = MockAttribute(self)
        self._asserters.append(ma.verify)
        return FunctionName(ma, attribute='funcdef')
    
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
        self.mock.reset_mock()
    
    def __getattr__(self, name):
        self._access_log.append(name)
        return getattr(self.mock, name)