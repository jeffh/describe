from unittest import TestCase
from mock import Mock, patch

from describe.mock.stubs import (ArgMatcher, Stub, AttributeArgument,
        ExpectationBuilder, ArgsTable, NoArgMatchError, Counter)
from describe import flags


class DescribeStubIntegratedAPI(TestCase):
    def test_magic_methods(self):
        die = Stub()
        die.__eq__.expects(flags.ANYTHING).and_returns(False)
        die.__eq__.expects(2).and_returns(True)

        self.assertEqual(die, 2)
        self.assertFalse(die == 3)


    def test_method_count_assertions(self):
        die = Stub().expects.roll(2).at_least(2).and_returns(True)
        die.expects.roll(3).at_most(1).and_returns(True)
        die.expects.roll(4).exactly(3).and_returns(True)

        die.roll(2)
        die.roll(2)
        die.roll(3)
        die.roll(4)
        die.roll(4)
        die.roll(4)

        die.verify_expectations()


    def test_it_can_expect_calls_with_flags(self):
        stub = Stub()
        stub.expects(flags.ANY_ARG).and_returns('foo')
        self.assertEqual(stub(1), 'foo')
        self.assertEqual(stub(2), 'foo')
        stub.verify_expectations()

    def test_it_can_expect_calls_without_explicit_returns(self):
        stub = Stub()
        stub.expects()
        self.assertTrue(isinstance(stub(), Stub))

    def test_it_can_expect_calls(self):
        stub = Stub().expects().and_returns('bar')
        self.assertEqual(stub(), 'bar')
        stub.verify_expectations()

    def test_it_can_expect_item_access(self):
        stub = Stub()
        stub.expects[1].and_returns('5')
        self.assertEqual(stub[1], '5')
        stub.verify_expectations()

    def test_it_raises_error_if_expected_call_not_invoked(self):
        stub = Stub()
        stub.expects()
        with self.assertRaises(AssertionError):
            stub.verify_expectations()

    def test_it_can_expect_child_calls(self):
        stub = Stub().expects.foo().and_returns('bar')
        self.assertEqual(stub.foo(), 'bar')
        stub.verify_expectations()

    def test_it_can_expect_child_item_access(self):
        stub = Stub()
        stub.expects.foo[0].and_returns('5')
        self.assertEqual(stub.foo[0], '5')
        stub.verify_expectations()

    def test_it_raises_error_if_expected_call_not_invoked_from_child(self):
        stub = Stub()
        stub.expects.foo()
        with self.assertRaises(AssertionError):
            stub.verify_expectations()


class DescribeCounter(TestCase):
    def test_it_can_increment_its_value(self):
        counter = Counter()
        counter.increment()
        self.assertEqual(counter.current, 1)
        counter.increment()
        self.assertEqual(counter.current, 2)

    def test_it_can_be_set_after_construction(self):
        counter = Counter()
        counter.set(4)
        self.assertEqual(counter.current, 4)

    def test_it_defaults_to_no_goal(self):
        counter = Counter()
        self.assertTrue(counter.verify())

    def test_it_does_not_fail_if_no_goal_is_set(self):
        counter = Counter()
        counter.set_goal(None)
        self.assertTrue(counter.verify())

    def test_it_uses_goal_as_an_assertion(self):
        counter = Counter(start=10)
        counter.set_goal(lambda c: c > 10)
        self.assertFalse(counter.verify())

        counter.increment()
        self.assertTrue(counter.verify())


class DescribeStubMagicMethods(TestCase):
    def setUp(self):
        self.stub = Stub()

    def assertStubInspect(self, obj, name, call_args):
        self.assertTrue(isinstance(obj, Stub), "Got %r instead of Stub instance" % obj)
        print getattr(self.stub, name)
        self.assertEqual(getattr(self.stub, name).call_args, call_args)

    def test_it_should_return_stub_from_operators(self):
        args = [((2,), {})]
        self.assertStubInspect(self.stub * 2, '__mul__', args)
        self.assertStubInspect(2 * self.stub, '__rmul__', args)

        self.assertStubInspect(self.stub / 2, '__div__', args)
        self.assertStubInspect(2 / self.stub, '__rdiv__', args)

        self.assertStubInspect(self.stub - 2, '__sub__', args)
        self.assertStubInspect(2 - self.stub, '__rsub__', args)

        self.assertStubInspect(self.stub + 2, '__add__', args)
        self.assertStubInspect(2 + self.stub, '__radd__', args)

        self.assertStubInspect(self.stub // 2, '__floordiv__', args)
        self.assertStubInspect(2 // self.stub, '__rfloordiv__', args)

        self.assertStubInspect(self.stub << 2, '__lshift__', args)
        self.assertStubInspect(2 << self.stub, '__rlshift__', args)

        self.assertStubInspect(self.stub >> 2, '__rshift__', args)
        self.assertStubInspect(2 >> self.stub, '__rrshift__', args)

        self.assertStubInspect(self.stub ** 2, '__pow__', args)
        self.assertStubInspect(2 ** self.stub, '__rpow__', args)

        self.assertStubInspect(self.stub & 2, '__and__', args)
        self.assertStubInspect(2 & self.stub, '__rand__', args)

        self.assertStubInspect(self.stub | 2, '__or__', args)
        self.assertStubInspect(2 | self.stub, '__ror__', args)

        self.assertStubInspect(self.stub ^ 2, '__xor__', args)
        self.assertStubInspect(2 ^ self.stub, '__rxor__', args)

        self.assertStubInspect(self.stub % 2, '__mod__', args)
        self.assertStubInspect(2 % self.stub, '__rmod__', args)

    def test_it_should_return_stub_on_unary_operators(self):
        args = [((), {})]
        self.assertStubInspect(-self.stub, '__neg__', args)
        self.assertStubInspect(+self.stub, '__pos__', args)
        self.assertStubInspect(abs(self.stub), '__abs__', args)
        self.assertStubInspect(~self.stub, '__invert__', args)

    def test_it_should_support_with_statement(self):
        stub = Stub()
        with stub as s:
            self.assertStub(s)


class DescribeStub(TestCase):
    def assertStub(self, obj):
        self.assertTrue(isinstance(obj, Stub), "Got %r instead of Stub instance" % obj)

    def test_it_should_restore_attribute_after_verifying(self):
        parent = Mock()
        oldvalue = parent.foo
        stub = Stub.attr(parent, 'foo')

        self.assertEqual(parent.foo, stub)
        stub.verify_expectations()
        self.assertEqual(parent.foo, oldvalue)

    def test_it_should_return_stubs(self):
        stub = Stub()
        self.assertStub(stub.foo)

    def test_it_should_returns_same_stub_object_for_same_attr(self):
        stub = Stub()
        self.assertTrue(stub.foo is stub.foo)

    def test_it_should_record_call_args(self):
        stub = Stub()
        r1 = stub()
        r2 = stub('foo')
        r3 = stub(foo='bar')
        self.assertTrue(r1 is r2 is r3)
        self.assertEqual(stub.call_args, [
            ((), {}),
            (('foo',), {}),
            ((), {'foo': 'bar'}),
        ])

    def test_it_should_convert_to_types(self):
        stub = Stub()
        self.assertEqual(list(stub), [stub.__iter__])

    def test_it_should_accept_assignment_of_properties(self):
        stub = Stub().with_attrs(cake='cake')
        self.assertEqual(stub.cake, 'cake')

    def test_it_should_accept_assignment_of_class_properties(self):
        stub = Stub().with_class_attrs(
            roll=lambda s: 4, cake='cake', __eq__=lambda s, o: True)
        self.assertEqual(stub.roll(), 4)
        self.assertEqual(stub.__class__.cake, 'cake')
        self.assertEqual(stub, None)

    def test_it_should_record_method_invocations(self):
        stub = Stub()
        stub.foo.bar('lol', a=1)
        self.assertEqual(stub.foo.bar.call_args, [
            (('lol',), {'a': 1}),
        ])

    def test_it_should_support_key_access(self):
        stub = Stub()
        self.assertIs(stub['foo'], stub['foo'])
        self.assertStub(stub['foo'])

    def test_it_should_support_key_setting(self):
        stub = Stub()
        stub['foo'] = 'bar'
        self.assertEqual(stub['foo'], 'bar')

    # I don't know how to do this yet. Maybe never do
    #def test_it_can_change_parents(self):
    #    stub = Stub()
    #    stub.inherits(int)
    #    self.assertTrue(isinstance(stub, int))


class DescribeArgsTable(TestCase):
    def test_it_should_match_nothing_by_default(self):
        at = ArgsTable()
        with self.assertRaises(NoArgMatchError):
            at()

    def test_it_should_invoke_default_func_if_no_match(self):
        result = Mock()
        m = Mock(return_value=result)
        at = ArgsTable(default=m)
        self.assertEqual(at('foo', {'bar': 1}), result)
        m.assert_called_once_with('foo', {'bar': 1})

    @patch('describe.mock.stubs.ArgMatcher')
    def test_it_invoke_lookup_func_if_matches(self, ArgMatcher):
        instance = ArgMatcher.return_value
        instance.matches.return_value = True

        at = ArgsTable()
        fn = Mock(return_value=3)

        at.add(fn, (flags.ANY_ARG,), {})
        self.assertEqual(at(1), 3)
        ArgMatcher.assert_called_once_with((flags.ANY_ARG,), {})
        instance.matches.assert_called_once_with((1,), {})
        fn.assert_called_once_with(1)

    @patch('describe.mock.stubs.ArgMatcher')
    def test_it_makes_newer_matches_take_precedence(self, ArgMatcher):
        instance = ArgMatcher.return_value
        instance.matches.return_value = True

        at = ArgsTable()
        fn1, fn2 = Mock(return_value=3), Mock(return_value=2)

        at.add(fn1, (flags.ANYTHING,), {})
        at.add(fn2, (flags.ANYTHING,), {})

        self.assertEqual(at(2), 2)
        fn2.assert_called_once_with(2)
        self.assertEqual(fn1.call_count, 0)


class DescribeAttributeArgument(TestCase):
    def setUp(self):
        self.m = Mock()
        self.attr = Mock()
        self.item = Mock()
        self.call = Mock()
        self.subject = AttributeArgument(self.m, self.attr, self.item, self.call)

    def test_it_should_build_from_getattr(self):
        self.subject.foo
        self.attr.assert_called_once_with('foo')

    def test_it_should_build_from_getitem(self):
        self.subject['foobar']
        self.item.assert_called_once_with('foobar')

    def test_it_should_build_from_call(self):
        self.subject('args', kwargs=1)
        self.call.assert_called_once_with(('args',), {'kwargs': 1})


class DescribeExpectationBuilderCallCounts(TestCase):
    def setUp(self):
        self.counter = Mock()

        self.stub = Mock()
        self.stub._argstable.get_by_func.return_value = (Mock(), Mock(), self.counter)

        self.subject = ExpectationBuilder(self.stub)

    def test_it_can_expect_counts(self):
        self.subject.exactly(5)

        self.assertEqual(self.counter.set_goal.call_count, 1)
        goalfn = self.counter.set_goal.call_args[0][0]
        self.assertTrue(goalfn(5))
        self.assertFalse(goalfn(4))
        self.assertFalse(goalfn(6))

    def test_it_can_expect_at_least(self):
        self.subject.at_least(5)

        self.assertEqual(self.counter.set_goal.call_count, 1)
        goalfn = self.counter.set_goal.call_args[0][0]
        self.assertTrue(goalfn(5))
        self.assertFalse(goalfn(4))
        self.assertTrue(goalfn(6))

    def test_it_can_expect_at_most(self):
        self.subject.at_most(5)

        self.assertEqual(self.counter.set_goal.call_count, 1)
        goalfn = self.counter.set_goal.call_args[0][0]
        self.assertTrue(goalfn(5))
        self.assertTrue(goalfn(4))
        self.assertFalse(goalfn(6))

class DescribeExpectationBuilder(TestCase):
    @patch('describe.mock.stubs.ValueConsumer')
    def test_it_can_invoke_multiple_values(self, ValueConsumer):
        instance = ValueConsumer.return_value
        stub = Mock()
        subject = ExpectationBuilder(stub)

        subject.and_returns(1, 2, 3)
        subject.invoke('a', foo='bar')

        ValueConsumer.assert_called_once_with((1, 2, 3))
        instance.assert_called_once_with('a', foo='bar')

    @patch('describe.mock.stubs.IteratorConsumer')
    def test_it_can_yield_iterator(self, IteratorConsumer):
        instance = IteratorConsumer.return_value
        stub = Mock()
        subject = ExpectationBuilder(stub)

        subject.and_yields(1, 2, 3)
        subject.invoke('a', foo='bar')

        IteratorConsumer.assert_called_once_with((1, 2, 3))
        instance.assert_called_once_with('a', foo='bar')

    @patch('describe.mock.stubs.FunctionConsumer')
    def test_it_can_yield_iterator(self, FunctionConsumer):
        instance = FunctionConsumer.return_value
        stub = Mock()
        subject = ExpectationBuilder(stub)

        subject.and_calls(lambda: 1, lambda: 2, lambda: 3)
        subject.invoke('a', foo='bar')

        FunctionConsumer.assert_called_once_with((1, 2, 3))
        instance.assert_called_once_with('a', foo='bar')

    @patch('describe.mock.stubs.ErrorConsumer')
    def test_it_can_yield_iterator(self, ErrorConsumer):
        instance = ErrorConsumer.return_value
        stub = Mock()
        subject = ExpectationBuilder(stub)

        funcs = (Mock(), Mock(), Mock())
        subject.and_raises(*funcs)
        subject.invoke('a', foo='bar')

        ErrorConsumer.assert_called_once_with(funcs)
        instance.assert_called_once_with('a', foo='bar')

    def test_it_should_accept_getitem(self):
        stub = Mock()
        subject = ExpectationBuilder(stub)
        subject.at_least = Mock()
        subject.build_getitem = Mock()
        subject['foo']
        subject.build_getitem.assert_called_once_with('foo')

    def test_it_should_accept_call(self):
        stub = Mock()
        subject = ExpectationBuilder(stub)
        subject.build_call = Mock()
        subject('foo', kwarg=2)
        subject.build_call.assert_called_once_with(('foo',), {'kwarg': 2})

    def test_build_call_should_add_matcher(self):
        stub = Mock()
        subject = ExpectationBuilder(stub)
        subject.at_least = Mock()
        subject.build_call(('foo',), {'bar': 1})
        stub._argstable.add(subject.invoke, ('foo',), {'bar': 1})

    def test_build_getattr_should_return_expectation_builder(self):
        stub = Mock()
        subject = ExpectationBuilder(stub)
        result = subject.build_getattr('name')
        self.assertTrue(isinstance(result, ExpectationBuilder))


class DescribeMock(TestCase):
    @patch('describe.mock.stubs.ExpectationBuilder')
    @patch('describe.mock.stubs.AttributeArgument')
    def test_it_provides_attribute_argument_object(self, AttributeArgument, ExpectationBuilder):
        builder = ExpectationBuilder.return_value
        attrarg = AttributeArgument.return_value

        stub = Stub()
        self.assertEqual(stub.expects, attrarg)
        ExpectationBuilder.assert_called_once_with(stub)
        AttributeArgument.assert_called_once_with(
            stub, builder.build_getattr, builder.build_getitem, builder.build_call)


class DescribeEmptyArgMatcher(TestCase):
    def setUp(self):
        self.am = ArgMatcher()

    def test_it_should_default_empty_args(self):
        self.assertTrue(self.am.matches((), {}))

    def test_it_should_not_match_args(self):
        self.assertFalse(self.am.matches((1,)))

    def test_it_should_not_match_anything_else(self):
        self.assertFalse(self.am.matches((1,), {}))
        self.assertFalse(self.am.matches((), {'foo': 'bar'}))


class DescribeEqualityArgMatcher(TestCase):
    def test_it_should_match_equal_args(self):
        am = ArgMatcher(args=(1, 2, 3))
        self.assertTrue(am.matches(args=(1, 2, 3)))

    def test_it_should_match_equal_kwargs(self):
        am = ArgMatcher(kwargs={'a': 1, 'b': 2})
        self.assertTrue(am.matches(kwargs={'a': 1, 'b': 2}))


class DescribeANY_ARGFlagForArgMatcher(TestCase):
    def test_it_should_match_argument(self):
        am = ArgMatcher((flags.ANY_ARG,))
        self.assertTrue(am.matches((1,)))

    def test_it_should_not_match_extra_args(self):
        am = ArgMatcher((flags.ANY_ARG,))
        self.assertFalse(am.matches((1, 2,)))

    def test_it_should_match_argument_plus_regular_value(self):
        am = ArgMatcher((flags.ANY_ARG, 2))
        self.assertTrue(am.matches((1, 2)))

    def test_it_should_not_match_if_regular_value_isnt(self):
        am = ArgMatcher((flags.ANY_ARG, 2))
        self.assertFalse(am.matches((1, 3,)))

    def test_3_flags_should_match_any_3_arguments(self):
        am = ArgMatcher((flags.ANY_ARG, flags.ANY_ARG, flags.ANY_ARG))
        self.assertTrue(am.matches((1, 2, 3)))

    def test_3_flags_should_not_match_any_2_arguments(self):
        am = ArgMatcher((flags.ANY_ARG, flags.ANY_ARG, flags.ANY_ARG))
        self.assertFalse(am.matches((1, 3)))

    def test_it_should_match_kwargs(self):
        am = ArgMatcher(kwargs={'a': flags.ANY_ARG})
        self.assertTrue(am.matches(kwargs={'a': 9}))

    def test_it_should_not_match_extra_kwargs(self):
        am = ArgMatcher(kwargs={'a': flags.ANY_ARG, 'b': 3})
        self.assertTrue(am.matches(kwargs={'a': 9, 'b': 3}))

    def test_3_flags_should_match_any_3_kwargs_values(self):
        am = ArgMatcher(kwargs={'a': flags.ANY_ARG, 'b': flags.ANY_ARG, 'c': flags.ANY_ARG})
        self.assertTrue(am.matches(kwargs={'a': 1, 'b': 2, 'c': 3}))

    def test_3_flags_should_not_match_any_2_kwarg_values(self):
        am = ArgMatcher(kwargs={'a': flags.ANY_ARG, 'b': flags.ANY_ARG})
        self.assertFalse(am.matches(kwargs={'a': 1, 'b': 2, 'c': 3}))


class DescribeANYTHINGFlagForArgMatcher(TestCase):
    def test_it_should_match_anything(self):
        am = ArgMatcher((flags.ANYTHING,))
        self.assertTrue(am.matches((1, 2, 3)))
        self.assertTrue(am.matches(kwargs={'foo': 'bar'}))
        self.assertTrue(am.matches((1, 2, 3), {'foo': 'bar'}))

    def test_it_should_raise_assertion_error_if_ANYTHING_is_not_only_thing_in_args(self):
        with self.assertRaises(AssertionError):
            ArgMatcher((flags.ANYTHING, 1))

    def test_it_should_raise_assertion_error_if_ANYTHING_and_kwargs_are_given(self):
        with self.assertRaises(AssertionError):
            ArgMatcher((flags.ANYTHING,), kwargs={'yeah': 1})

    def test_it_should_raise_assertion_error_if_ANYTHING_is_in_kwargs(self):
        with self.assertRaises(AssertionError):
            ArgMatcher(kwargs={'a': flags.ANYTHING})

        with self.assertRaises(AssertionError):
            ArgMatcher(kwargs={flags.ANYTHING: 3})


class DescribeANY_ARGSFlagForArgMatcher(TestCase):
    def test_it_should_match_any_args(self):
        am = ArgMatcher((flags.ANY_ARGS,))
        self.assertTrue(am.matches((1, 2, 3)))
        self.assertTrue(am.matches((1, 2, 'foo')))
        self.assertTrue(am.matches((2, 'foo')))
        self.assertTrue(am.matches(()))

    def test_it_should_not_match_any_kwargs(self):
        am = ArgMatcher((flags.ANY_ARGS,))
        self.assertFalse(am.matches(kwargs={'a': 1}))
        self.assertFalse(am.matches((1, 2, 3), {'a': 1}))


class DescribeANY_KWARGSFlagForArgMatcher(TestCase):
    def test_it_should_match_any_kwargs(self):
        am = ArgMatcher((flags.ANY_KWARGS,))
        self.assertTrue(am.matches(kwargs={'a': 2, 'b': 'foo'}))
        self.assertTrue(am.matches(kwargs={'a': 3, 'b': 'foo'}))
        self.assertTrue(am.matches(()))

    def test_it_should_not_match_any_kwargs(self):
        am = ArgMatcher((flags.ANY_ARGS,))
        self.assertFalse(am.matches(kwargs={'a': 1}))
        self.assertFalse(am.matches((1, 2, 3), {'a': 1}))


class DescribeFlagCombinationsForArgMatcher(TestCase):
    def test_ANY_ARGS_and_ANY_KWARGS_matches_anything(self):
        am = ArgMatcher((flags.ANY_ARGS, flags.ANY_KWARGS))
        self.assertTrue(am.matches((1, 2, 3)))
        self.assertTrue(am.matches(kwargs={'foo': 'bar'}))
        self.assertTrue(am.matches((1, 2, 3), {'foo': 'bar'}))

