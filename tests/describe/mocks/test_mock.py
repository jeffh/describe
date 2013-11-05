from unittest import TestCase

from describe.mock.mock import (
    Mock, Invoke, verify_mock, MockErrorDelegate,
)
from describe.mock.expectations import ExpectationList, ExpectationSet, Expectation
from describe import flags as f


class TestMockExpectationIntegration(TestCase):
    def test_it_can_be_instance_of(self):
        class Foo(object):
            pass
        m = Mock(instance_of=Foo)
        m.expects.foo().and_returns(1)
        self.assertTrue(isinstance(m, Foo))
        self.assertEqual(m.foo(), 1)

    def test_it_can_return_attr(self):
        m = Mock()
        m.expects.foo.and_returns(2)
        self.assertEqual(m.foo, 2)

    def test_it_can_return_multiple(self):
        m = Mock()
        m.expects.foo.and_returns(1, 2, 3)
        self.assertEqual(m.foo, 1)
        self.assertEqual(m.foo, 2)
        self.assertEqual(m.foo, 3)

    def test_it_can_return_generator(self):
        m = Mock()
        m.expects.foo().and_yields(1, 2, 3)
        self.assertEqual(list(m.foo()), [1, 2, 3])

    def test_it_can_return_from_function(self):
        m = Mock()
        m.expects.foo().and_calls(lambda: 1, lambda: 2)
        self.assertEquals(m.foo(), 1)
        self.assertEquals(m.foo(), 2)

    def test_it_should_raise_error(self):
        m = Mock()
        m.expects.foo().and_raises(TypeError)
        with self.assertRaises(TypeError):
            m.foo()
        with self.assertRaises(AssertionError):
            m.foo()

    def test_it_should_return_expectation(self):
        m = Mock()
        m.expects.foo().and_returns(4)
        self.assertEqual(m.foo(), 4)
        with self.assertRaises(AssertionError):
            m.foo()

    def test_it_can_expect_item_access(self):
        m = Mock()
        m.expects['foo'].and_returns(4)
        with self.assertRaises(AssertionError):
            m['bar']
        self.assertEqual(m['foo'], 4)
        with self.assertRaises(AssertionError):
            m['foo']

    def test_it_can_expect_invocation(self):
        m = Mock()
        m.expects().and_returns(4)
        with self.assertRaises(AssertionError):
            m('foo')
        self.assertEqual(m(), 4)
        with self.assertRaises(AssertionError):
            m()

    def test_it_should_return_for_magic_method(self):
        m = Mock()
        m.expects.__eq__(f.ANYTHING).and_returns(True)
        self.assertTrue(m == 4)

    def test_it_should_expect_arguments(self):
        m = Mock()
        m.expects.foo(3).and_returns(2)
        with self.assertRaises(AssertionError):
            m.foo()
        with self.assertRaises(AssertionError):
            m.foo(1)
        self.assertEqual(m.foo(3), 2)
        with self.assertRaises(AssertionError):
            m.foo(3)

class TestEmptyMock(TestCase):
    def test_it_should_raise_on_invalid_attr_access(self):
        m = Mock()
        with self.assertRaises(AssertionError):
            m.attr

    def test_it_should_raise_error_on_invalid_invocation(self):
        m = Mock()
        with self.assertRaises(AssertionError):
            m()

    def test_it_should_raise_error_on_invalid_magic_methods(self):
        m = Mock()
        with self.assertRaises(AssertionError):
            m + 2

    def test_validates(self):
        m = Mock()
        verify_mock(m)

class TestMocksWithSharedExpectationList(TestCase):
    def setUp(self):
        self.d = MockErrorDelegate()
        self.expectation_list = ExpectationList(delegate=self.d)
        self.m1 = Mock(expectations=self.expectation_list)
        self.m2 = Mock(expectations=self.expectation_list)
        self.m1.expects.foo().and_returns(1)
        self.m2.expects.foo().and_returns(2)
        self.m1.expects.bar().and_returns(3)

    def test_it_passes_if_all_methods_to_be_ordered_across_objects(self):
        self.assertEquals(self.m1.foo(), 1)
        self.assertEquals(self.m2.foo(), 2)
        self.assertEquals(self.m1.bar(), 3)
        verify_mock(self.m1)
        verify_mock(self.m2)

    def test_it_fails_if_not_all_methods_were_called_for_that_mock(self):
        self.assertEquals(self.m1.foo(), 1)
        self.assertEquals(self.m2.foo(), 2)
        verify_mock(self.m2)
        with self.assertRaises(AssertionError):
            verify_mock(self.m1)

    def test_it_fails_if_methods_are_not_invoked_on_the_correct_object(self):
        self.assertEquals(self.m1.foo(), 1)
        with self.assertRaises(AssertionError):
            self.m1.foo()

    def test_it_fails_if_methods_are_not_invoked_in_the_correct_order(self):
        self.assertEquals(self.m1.foo(), 1)
        print self.expectation_list
        with self.assertRaises(AssertionError):
            self.m1.bar()

    def test_it_fails_if_methods_are_not_invoked_in_the_correct_order_of_objects(self):
        with self.assertRaises(AssertionError):
            self.m2.foo()

class TestMockWithExpectationList(TestCase):
    def setUp(self):
        self.d = MockErrorDelegate()

    def test_it_does_not_validate(self):
        m = Mock(expectations=ExpectationList(Expectation(None, 'foo', returns=42), delegate=self.d))
        with self.assertRaises(AssertionError):
            verify_mock(m)

    def test_it_can_raise_error(self):
        m = Mock(error_delegate=self.d)
        m.expects.foo().and_raises(TypeError)
        with self.assertRaises(TypeError):
            m.foo()

    def test_it_should_allow_attr_access_with_expectation(self):
        m = Mock(expectations=ExpectationList(Expectation(None, 'foo', returns=42), delegate=self.d))
        self.assertEqual(m.foo, 42)
        with self.assertRaises(AssertionError):
            m.foo

    def test_it_should_allow_method_invocation_with_expectations(self):
        m = Mock(error_delegate=self.d)
        m.expects.foo().and_returns(2)
        self.assertEqual(m.foo(), 2)
        with self.assertRaises(AssertionError):
            m.foo()

    def test_it_expects_specified_ordering(self):
        m = Mock()
        m.expects.foo().and_returns(2)
        m.expects.bar().and_returns(3)
        with self.assertRaises(AssertionError):
            m.bar()
        self.assertEqual(m.foo(), 2)
        self.assertEqual(m.bar(), 3)
        with self.assertRaises(AssertionError):
            m.foo()

    def test_it_should_allow_call_with_expectations(self):
        m = Mock()
        m.expects.__call__().and_returns(1)
        self.assertEqual(m(), 1)
        with self.assertRaises(AssertionError):
            m()

    def test_it_should_allow_magic_methods_with_expectations(self):
        m = Mock()
        m.expects.__add__(f.ANYTHING).and_returns(4)
        self.assertEqual(m + 2, 4)
        with self.assertRaises(AssertionError):
            m + 2

    def test_it_should_allow_multiple_calls_to_same_method_with_expectations(self):
        m = Mock(error_delegate=self.d)
        m.expects.foo().and_returns(1)
        m.expects.foo().and_returns(2)
        self.assertEqual(m.foo(), 1)
        self.assertEqual(m.foo(), 2)
        with self.assertRaises(AssertionError):
            m.foo()

class TestMockWithExpectationSet(TestCase):
    def setUp(self):
        self.d = MockErrorDelegate()

    def test_it_expects_regardless_of_order(self):
        m = Mock(ordered=False)
        m.expects.foo().and_returns(2)
        m.expects.bar().and_returns(4)
        self.assertEqual(m.bar(), 4)
        self.assertEqual(m.foo(), 2)

    def test_it_should_allow_multiple_calls_to_same_method_with_expectations(self):
        m = Mock()
        m.expects.foo().and_returns(1)
        m.expects.foo().and_returns(2)
        self.assertEqual(m.foo(), 1)
        self.assertEqual(m.foo(), 2)
        with self.assertRaises(AssertionError):
            m.foo()

