from describe import *
from describe.mock.args_matcher import ArgList
from describe.mock.args_filter import *
import unittest
from bowling import Bowling

class NumericArgListShould(unittest.TestCase):
    def setUp(self):
        self.v = (1,2,3,4,5)
        self.al = Value(ArgList(self.v))
    
    def test_match_self(self):
        self.al.should == ArgList(self.v)
        
    def test_not_match_another_numberset(self):
        self.al.should_not == ArgList((1,2,3,4,6))
        
    def test_not_match_nothing(self):
        self.al.should_not == ArgList()

class AnythingArgListShould(unittest.TestCase):
    def setUp(self):
        self.arglist = Value(ArgList(args=(ANYTHING,)))
    
    def test_match_nothing(self):
        self.arglist.should == ArgList()
    
    def test_match_single_arg(self):
        self.arglist.should == ArgList(('foo',), {})
    
    def test_match_single_kwarg(self):
        self.arglist.should == ArgList((), {'foo': 3})
        
    def test_match_args_and_kwargs(self):
        self.arglist.should == ArgList((65,), {'foo': 3})
        
class AnyArgArgListShould(unittest.TestCase):
    def setUp(self):
        self.al = Value(ArgList(args=(ANY_ARG,)))
    
    def test_not_match_nothing(self):
        self.al.should_not == ArgList()
        
    def test_match_single_arg(self):
        self.al.should == ArgList((1,))
        
    def test_not_match_two_args(self):
        self.al.should_not == ArgList(('bat','man'))
        
    def test_not_match_single_kwarg(self):
        self.al.should_not == ArgList((), {'foo': 3})
        
    def test_match_ANYTHING(self):
        self.al.should == ArgList((ANYTHING,))

class SplatArgsArgListShould(unittest.TestCase):
    def setUp(self):
        self.al = Value(ArgList(args=(ARGS,)))
    
    def test_match_nothing(self):
        self.al.should == ArgList()
        
    def test_match_single_arg(self):
        self.al.should == ArgList((1,))
    
    def test_match_two_args(self):
        self.al.should == ArgList((1, 'foo'))
        
    def test_not_match_kwarg(self):
        self.al.should_not == ArgList(kwargs={'foobar':1})
        
    def test_not_match_args_and_kwargs(self):
        self.al.should_not == ArgList((1,2,3), {'size':3})
        
class DoubleSplatKwargsArgListShould(unittest.TestCase):
    def setUp(self):
        self.al = Value(ArgList((KWARGS,)))
        
    def test_match_nothing(self):
        self.al.should == ArgList()
        
    def test_not_match_single_arg(self):
        self.al.should_not == ArgList((1,))
    
    def test_not_match_two_args(self):
        self.al.should_not == ArgList((1, 'foo'))
        
    def test_match_kwarg(self):
        self.al.should == ArgList(kwargs={'foobar':1})
        
    def test_not_match_args_and_kwargs(self):
        self.al.should_not == ArgList((1,2,3), {'size':3})
    
    def test_match_two_kwargs(self):
        self.al.should == ArgList(kwargs={'cow':'moo', 'cat':'meow'})
        
class InstanceOfArgListShould(unittest.TestCase):
    def test_match_instance_of_str(self):
        Value(ArgList((an_instance_of(str),))).should == ArgList(('foo',))
        
    def test_not_match_instance_of_str(self):
        Value(ArgList((an_instance_of(str),))).should_not == ArgList((1,))
        
    def test_match_instance_of_int(self):
        Value(ArgList((an_instance_of(int),))).should == ArgList((1,))

    def test_not_match_instance_of_int(self):
        Value(ArgList((an_instance_of(int),))).should_not == ArgList(('foo',))
        
    def test_match_instance_of_bool(self):
        Value(ArgList((boolean,))).should == ArgList((True,))

    def test_not_match_instance_of_bool(self):
        Value(ArgList((boolean,))).should_not == ArgList((1,))

class IncludesPairArgListShould(unittest.TestCase):
    def setUp(self):
        self.al = Value(ArgList((dict_includes({'foo': 'bar'}),)))
    
    def test_not_match_nothing(self):
        self.al.should_not == ArgList()
        
    def test_not_match_single_non_dict_arg(self):
        self.al.should_not == ArgList((2,))
        
    def test_not_match_empty_dict(self):
        self.al.should_not == ArgList(({},))
        
    def test_match_with_keypair(self):
        self.al.should == ArgList(({'foo': 'bar'},))
        
    def test_match_with_keypair_and_other_keypairs(self):
        self.al.should == ArgList(({'foo': 'bar', 'cake': 'is a lie', 2: 9},))

    def test_not_match_with_other_keypairs(self):
        self.al.should_not == ArgList(({'cake': 'is a lie', 2: 9},))
        
    def test_not_match_with_tuple(self):
        self.al.should_not == ArgList(((),))
        
    def test_not_match_with_list(self):
        self.al.should_not == ArgList(([],))

    def test_match_with_dict_interface_with_keypair(self):
        class IDict(object):
            class RaiseException(object):
                pass
            def __init__(self, **kwargs):
                self.kwargs = kwargs
                
            def __iter__(self):
                return iter(self.kwargs)
                
            def get(self, key, default=RaiseException):
                try:
                    return self.kwargs[key]
                except KeyError:
                    if default == RaiseException:
                        raise
                    else:
                        return default
        
        self.al.should == ArgList((IDict(foo='bar'),))

class DuckTypeGetMethodArgListShould(unittest.TestCase):
    def setUp(self):
        self.al = Value(ArgList((duck_type('get'),)))
        
    def test_match_with_dict(self):
        self.al.should == ArgList(({},))
        
    def test_not_match_list(self):
        self.al.should_not == ArgList(([],))
        
    def test_not_match_int(self):
        self.al.should_not == ArgList((1,))
        
