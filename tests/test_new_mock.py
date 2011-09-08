from describe import Value, Mock
from describe.mock.args_filter import *
from describe.mock import repository
from describe.spec import Spec, fails_verification

class DescribeRSpecExpectingArguments(Spec):
    def before(self):
        self.m = Mock()

    def it_should_expect_arguments(self):
        self.m.should_access.msg(1,2,3)
        self.m.msg(1,2,3)

    def it_should_expect_arguments_with_count(self):
        self.m.should_access.msg(1,2,3).once
        self.m.msg(1,2,3)

    def it_should_expect_no_arguments(self):
        self.m.should_access.msg()
        self.m.msg()

    def it_should_expect_any_arguments(self):
        self.m.should_access.msg(ANYTHING)
        self.m.msg(1,2,3,4,5,6)


class DescribeRSpecArgumentConstraints(Spec):
    def before(self):
        self.m = Mock()

    def it_should_expect_any_argument(self):
        self.m.should_access.msg(1, ANY_ARG, "A")
        self.m.msg(1, 'foo', "A")

    def it_should_expect_an_instance_of(self):
        self.m.should_access.msg('a', an_instance_of(int), 'b')
        self.m.msg('a', 9, 'b')

    def it_should_expect_hash_including(self):
        self.m.should_access.msg('a', 'b', dict_includes({'c': 'd'}))
        self.m.msg('a', 'b', {'c': 'd', 'e': 'f'})

    @fails_verification
    def it_should_fail_when_expecting_hash_including(self):
        self.m.should_access.msg('a', 'b', dict_includes({'c': 'd'})).once
        self.m.msg('a', 'b', {'e': 'f'})

    def it_should_expect_bool(self):
        self.m.should_access.msg('a', boolean, 'b')
        self.m.msg('a', True, 'b')

    def it_should_expect_obj_that_responds_to(self):
        self.m.should_access.msg('a', duck_type('__abs__', '__div__'), 'b')
        self.m.msg('a', 5, 'b')


class DescribeRSpecReceiveCounts(Spec):
    def before(self):
        self.m = Mock()

    @fails_verification
    def it_should_fail_receiving_less_than_once(self):
        self.m.should_access.msg().once

    @fails_verification
    def it_should_fail_receiving_more_than_once(self):
        self.m.should_access.msg().once
        self.m.msg()
        self.m.msg()

    def it_should_receive_once(self):
        self.m.should_access.msg().once
        self.m.msg()

    @fails_verification
    def it_should_fail_receiving_less_than_twice(self):
        self.m.should_access.msg().twice

    @fails_verification
    def it_should_fail_receiving_more_than_twice(self):
        self.m.should_access.msg().twice
        self.m.msg()
        self.m.msg()
        self.m.msg()

    def it_should_receive_twice(self):
        self.m.should_access.msg().twice
        self.m.msg()
        self.m.msg()

    @fails_verification
    def it_should_fail_receiving_less_than_10_times(self):
        self.m.should_access.msg().exactly(10).times

    @fails_verification
    def it_should_fail_receiving_more_than_10_times(self):
        self.m.should_access.msg().exactly(10).times
        for i in range(15):
            self.m.msg()

    def it_should_receive_10_times(self):
        self.m.should_access.msg().exactly(10).times
        for i in range(10):
            self.m.msg()

    def it_should_receive_at_least_twice(self):
        self.m.should_access.msg().at_least('twice')
        self.m.msg()
        self.m.msg()

    def it_should_receive_at_least_once(self):
        self.m.should_access.msg().at_least('once')
        self.m.msg()

    def it_should_receive_at_least_once_when_called_more_than_once(self):
        self.m.should_access.msg().at_least('once')
        for i in range(5):
            self.m.msg()

    @fails_verification
    def it_should_fail_when_receiving_at_least_once(self):
        self.m.should_access.msg().at_least('once')

    def it_should_receive_at_most_twice_when_called_to_zero(self):
        self.m.should_access.msg().at_most('twice')
        self.m.msg()
        self.m.msg()

    def it_should_receive_at_most_twice(self):
        self.m.should_access.msg().at_most('twice')
        self.m.msg()
        self.m.msg()

    @fails_verification
    def it_should_fail_when_receiving_at_most_twice_when_called_more_than_twice(self):
        self.m.should_access.msg().at_most('twice')
        for i in range(5):
            self.m.msg()

    def it_should_explicitly_expect_imprecise_counts(self):
        self.m.should_access.msg().any_number_of_times

    def it_should_implicitly_expect_at_least_one(self):
        self.m.should_access.msg()
        self.m.msg()

class DescribeRSpecReturnValues(Spec):
    def before(self):
        self.m = Mock()

    def it_should_return_a_specific_value(self):
        self.m.should_access.msg().once.and_return('foo')
        Value(self.m).invoking.msg().should == 'foo'

    def it_should_return_consecutive_values(self):
        self.m.should_access.msg().and_return(0,1,2,3,4)
        for i in range(5):
            Value(self.m).invoking.msg().should == i

    def it_should_return_from_function(self):
        def func():
            return 'bar'
        self.m.should_access.msg().and_return_from_callable(func)
        Value(self.m).invoking.msg().should == 'bar'

    def it_should_return_yielded_values(self):
        # note: python yield is different from ruby's yield
        def func():
            yield 1
            yield 2
            yield 3
        self.m.should_access.msg().and_return_from_callable(func)

        for i,j in enumerate(self.m.msg()):
            Value(j).should == i + 1

class DescribeRSpecOrdering(Spec):
    def before(self):
        self.m = Mock()

    def it_should_receive_flip_before_flop(self):
        self.m.should_access.flip().once.ordered
        self.m.should_access.flop().once.ordered
        self.m.flip()
        self.m.flop()

    @fails_verification
    def it_should_fail_when_not_receiving_flip_before_flop(self):
        self.m.should_access.flip().once.ordered
        self.m.should_access.flop().once.ordered
        self.m.flop()
        self.m.flip()

    def it_should_receive_one_two_three_in_order(self):
        self.m.should_access.one().ordered
        self.m.should_access.two().ordered
        self.m.should_access.three().ordered

        self.m.one()
        self.m.two()
        self.m.three()

    @fails_verification
    def it_should_fail_when_receiving_one_two_three_not_in_order1(self):
        self.m.should_access.one().ordered
        self.m.should_access.two().ordered
        self.m.should_access.three().ordered

        self.m.two()
        self.m.one()
        self.m.three()

    @fails_verification
    def it_should_fail_when_receiving_one_two_three_not_in_order2(self):
        self.m.should_access.one().ordered
        self.m.should_access.two().ordered
        self.m.should_access.three().ordered

        self.m.two()
        self.m.three()
        self.m.one()

    @fails_verification
    def it_should_fail_when_receiving_one_two_three_not_in_order3(self):
        self.m.should_access.one().ordered
        self.m.should_access.two().ordered
        self.m.should_access.three().ordered

        self.m.one()
        self.m.three()
        self.m.two()

    def it_should_receive_one_two_in_order_but_others_do_not_matter(self):
        self.m.should_access.zero()
        self.m.should_access.one().ordered
        self.m.should_access.two().ordered

        self.m.one()
        self.m.one_and_a_half()
        self.m.zero()
        self.m.two()

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

    def should_mock_with_one_specific_arg(self):
        self.m.should_access.rjust(5).and_return(' ' * 5)
        Value(self.m).invoking.rjust(5).should == '     '

    @fails_verification
    def should_mock_invalid_args(self):
        self.m.should_access.rjust(5).and_return(' ' * 5)
        self.m.rjust(3)

    def should_raise_error_on_add_numbers(self):
        self.m.should_access.__add__(self.m, 3).and_raise(ValueError)
        (Value(self.m) + 3).should.raise_error(ValueError)

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

    @fails_verification
    def it_should_fail_when_requiring_bowl_to_be_called_10_times(self):
        self.m.should_access.bowl(ANY_ARG).and_return(70).exactly(10).times
        self.m.bowl(5)

    def it_should_require_bowl_to_be_called_10_times(self):
        self.m.should_access.bowl(ANY_ARG).and_return(70).exactly(10).times
        for i in range(10):
            self.m.bowl(i)

    def it_should_require_bowl_to_be_called_at_least_5_times(self):
        self.m.should_access.bowl(ANY_ARG).and_return(70).at_least(10).times
        for i in range(10):
            self.m.bowl(i)

    @fails_verification
    def it_should_fail_when_requiring_bowl_to_be_called_at_least_5_times(self):
        self.m.should_access.bowl(ANY_ARG).and_return(70).at_least(10).times
        for i in range(3):
            self.m.bowl(i)

    def it_should_require_bowl_to_be_called_at_most_8_times(self):
        self.m.should_access.bowl(ANY_ARG).and_return(70).at_most(8).times
        for i in range(7):
            self.m.bowl(i)

    @fails_verification
    def it_should_fail_when_requiring_bowl_to_be_called_at_most_8_times(self):
        self.m.should_access.bowl(ANY_ARG).and_return(70).at_most(8).times
        for i in range(10):
            self.m.bowl(i)

class DescribeRelaxedMock(Spec):
    def before(self):
        self.m = Mock(strict=False)

    def it_should_not_raise_error_on_random_invocation(self):
        self.m.foobar()

    def it_should_not_raise_error_on_random_invocations_with_certain_expectations(self):
        self.m.should_access.upper().and_return('bar')
        self.m.foobar()
        Value(self.m).invoking.upper().should == 'bar'

    @fails_verification
    def it_should_raise_error_when_certain_expectations_are_not_met(self):
        self.m.should_access.foobar()

class DescribeMockAttribute(Spec):
    def before(self):
        self.m = Mock()

    def it_should_allow_attribute_accessible(self):
        self.m.should_access.foo.and_return('bar')
        Value(self.m).get.foo.should == 'bar'

    def it_should_allow_attribute_writable(self):
        #self.should_write
        pass

