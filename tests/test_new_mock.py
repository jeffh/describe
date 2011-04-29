from describe import Value, Mock
from describe.mock.args_filter import *
from describe.mock import repository
from describe.spec import Spec, fails_verification
import unittest
from functools import wraps


def should_fail_verification(func):
    def decorated(self):
        self.should_fail = func.__name__
        return func(self)
    return wraps(func)(decorated)

class StrMock(Spec):
    def before(self):
        self.m = Mock()
        
    def should_allow_hook_expectations(self):
        self.m.should_access.__add__(self.m, 'bar').and_return('foobar')
        Value(self.m + 'bar').should == 'foobar'
        
    def should_allow_sequence_hook_expectations(self):
        self.m.should_access.__contains__(self.m, 'c').and_return(True)
        Value(self.m).should.contain('c')
        
    def should_allow_mock_verify_expectation(self):
        self.m.should_access.verify().and_return('bar')
        Value(self.m.mock).invoking.verify().should == 'bar'
        
    @fails_verification
    def should_mock_verification(self):
        self.m.should_access.upper().and_return('FOO')

    def should_mock_with_no_args(self):
        self.m.should_access.upper().and_return('FOO')
        Value(self.m).invoking.upper().should == 'FOO'
    
    def should_mock_with_no_access(self):
        self.m.should_not_access.upper()
        self.m.lower()

    def test_mock_with_one_specific_arg(self):
        self.m.should_access.rjust(5).and_return(' ' * 5)
        Value(self.m).invoking.rjust(5).should == '     '
    
    @fails_verification
    def test_mock_invalid_args(self):
        self.m.should_access.rjust(5).and_return(' ' * 5)
        self.m.rjust(3)
        
class DescribeListMock(Spec):
    def before(self):
        self.m = Mock()
    
    def it_should_allow_setitem_hook(self):
        self.m.should_access.__setitem__(self.m, 'foo', 'lol')
        self.m.should_access.__getitem__(self.m, 'foo').and_return('lol')
        self.m['foo'] = 'lol'
        Value(self.m).get['foo'].should == 'lol'

class DescribeBowlerMock(Spec):
    def before(self):
        self.m = Mock()
        
    def it_should_accept_specific_kwarg(self):
        self.m.should_access.bowl(score=8).and_return(80)
        Value(self.m).invoking.bowl(score=8).should == 80
    
    def it_should_allow_property_reads(self):
        self.m.should_access.score.and_return(0)
        Value(self.m).get.score.should == 0
    
    @fails_verification
    def it_should_require_it_to_be_called(self):
        self.m.should_access.set_scores(ANYTHING)
    
    def it_should_success_with_any_args(self):
        self.m.should_access.set_scores(ANYTHING)
        self.m.set_scores(5, 5, 7, 7, 10)
    