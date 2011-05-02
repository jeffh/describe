from describe import Spec, Value
from describe.utils import ellipses

class DescribeExpectationErrors(Spec):
    def before(self):
        self._tmp = Value.REPR_MAX_LENGTH
        Value.REPR_MAX_LENGTH = 20
    
    def after(self):
        Value.REPR_MAX_LENGTH = self._tmp
        
    def it_should_show_ellipses_list_repr_of_eq_comparison(self):
        list1, list2 = list(range(50)), list(reversed(range(50)))
        try:
            Value(list1).should == list2
        except AssertionError, e:
            msg = e.message
            assert ellipses(repr(list1), 20) in msg
            assert ellipses(repr(list2), 20) in msg
            
    def it_should_show_diff_in_dict_eq_comparison(self):
        dict1, dict2 = {'abc-key':'b'}, {'bcd-key': 'c'}
        try:
            Value(dict1).should == dict2
        except AssertionError, e:
            msg = e.message[e.message.index('\n'):]
            assert 'no value' in msg
            assert 'abc-key' in msg
            
    def it_should_show_diff_in_iterable_eq_comparison(self):
        eq_part = list(range(50, 75))
        list1, list2 = eq_part + list(range(50)), eq_part + list(reversed(range(50)))
        try:
            Value(list1).should == list2
        except AssertionError, e:
            msg = e.message
            assert '0' in msg and '49' in msg >= 0, msg
            assert '75' not in msg, msg
        
    def it_should_show_diff_in_iterable_equal_elements_to(self):
        eq_part = list(range(50, 75))
        list1, list2 = eq_part + list(range(50)), eq_part + list(reversed(range(50)))
        try:
            Value(list1).should.have_equal_elements_to(tuple(list2))
        except AssertionError, e:
            msg = e.message
            assert '0' in msg and '49' in msg >= 0, msg
            assert '75' not in msg, msg

