from unittest import TestCase

from describe.mock.mock import Mock, ExpectationList, ExpectationSet, Expectation, Invoke, verify_mock
from describe.mock.expectations import ExpectationList, ExpectationSet, Expectation
from describe import flags as f


class TestMockExpectationIntegration(TestCase):
	def test_it_can_be_instance_of(self):
		class Foo(object):
			pass
		m = Mock(instance_of=Foo)
		m.expects.foo().to_return(1)
		self.assertTrue(isinstance(m, Foo))
		self.assertEqual(m.foo(), 1)

	def test_it_can_return_attr(self):
		m = Mock()
		m.expects.foo.to_return(2)
		self.assertEqual(m.foo, 2)

	def test_it_should_raise_error(self):
		m = Mock()
		m.expects.foo().to_raise(TypeError)
		with self.assertRaises(TypeError):
			m.foo()
		with self.assertRaises(AssertionError):
			m.foo()

	def test_it_should_return_expectation(self):
		m = Mock()
		m.expects.foo().to_return(4)
		self.assertEqual(m.foo(), 4)
		with self.assertRaises(AssertionError):
			m.foo()

	def test_it_can_expect_item_access(self):
		m = Mock()
		m.expects['foo'].to_return(4)
		with self.assertRaises(AssertionError):
			m['bar']
		self.assertEqual(m['foo'], 4)
		with self.assertRaises(AssertionError):
			m['foo']

	def test_it_can_expect_invocation(self):
		m = Mock()
		m.expects().to_return(4)
		with self.assertRaises(AssertionError):
			m('foo')
		self.assertEqual(m(), 4)
		with self.assertRaises(AssertionError):
			m()

	def test_it_should_return_for_magic_method(self):
		m = Mock()
		m.expects.__eq__(f.ANYTHING).to_return(True)
		self.assertTrue(m == 4)

	def test_it_should_expect_arguments(self):
		m = Mock()
		m.expects.foo(3).to_return(2)
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


class TestMockWithExpectationList(TestCase):
	def test_it_does_not_validate(self):
		m = Mock()
		m.__expectations__ = ExpectationList(Expectation('foo', returns=42))
		with self.assertRaises(AssertionError):
			verify_mock(m)

	def test_it_can_raise_error(self):
		m = Mock()
		m.__expectations__ = ExpectationList(Expectation.raises('foo', TypeError))
		with self.assertRaises(TypeError):
			m.foo()

	def test_it_should_allow_attr_access_with_expectation(self):
		m = Mock()
		m.__expectations__ = ExpectationList(Expectation('foo', returns=42))
		self.assertEqual(m.foo, 42)
		with self.assertRaises(AssertionError):
			m.foo

	def test_it_should_allow_method_invocation_with_expectations(self):
		m = Mock()
		m.__invocations__ = set(('foo',))
		m.__expectations__ = ExpectationList(Expectation('foo', returns=Invoke(lambda: 2)))
		self.assertEqual(m.foo(), 2)
		with self.assertRaises(AssertionError):
			m.foo()

	def test_it_expects_specified_ordering(self):
		m = Mock()
		m.__invocations__ = set(('foo', 'bar'))
		m.__expectations__ = ExpectationList(
		    Expectation('foo', returns=Invoke(lambda: 2)),
		    Expectation('bar', returns=Invoke(lambda: 3)),
		)
		with self.assertRaises(AssertionError):
			m.bar()
		self.assertEqual(m.foo(), 2)
		self.assertEqual(m.bar(), 3)
		with self.assertRaises(AssertionError):
			m.foo()

	def test_it_should_allow_call_with_expectations(self):
		m = Mock()
		m.__invocations__ = set(('__call__',))
		m.__expectations__ = ExpectationList(Expectation('__call__', returns=1))
		self.assertEqual(m(), 1)
		with self.assertRaises(AssertionError):
			m()

	def test_it_should_allow_magic_methods_with_expectations(self):
		m = Mock()
		m.__invocations__ = set(('__add__',))
		m.__expectations__ = ExpectationList(Expectation('__add__', returns=4))
		self.assertEqual(m + 2, 4)
		with self.assertRaises(AssertionError):
			m + 2

	def test_it_should_allow_multiple_calls_to_same_method_with_expectations(self):
		m = Mock()
		m.__invocations__ = set(('foo',))
		m.__expectations__ = ExpectationList(Expectation('foo', returns=1), Expectation('foo', returns=2))
		self.assertEqual(m.foo(), 1)
		self.assertEqual(m.foo(), 2)
		with self.assertRaises(AssertionError):
			m.foo()

class TestMockWithExpectationSet(TestCase):
	def test_it_expects_regardless_of_order(self):
		m = Mock()
		m.__invocations__ = set(('foo', 'bar'))
		m.__expectations__ = ExpectationSet(Expectation('foo', returns=2), Expectation('bar', returns=4))
		self.assertEqual(m.bar(), 4)
		self.assertEqual(m.foo(), 2)

	def test_it_should_allow_multiple_calls_to_same_method_with_expectations(self):
		m = Mock()
		m.__invocations__ = set(('foo',))
		m.__expectations__ = ExpectationSet(Expectation('foo', returns=1), Expectation('foo', returns=2))
		self.assertEqual(m.foo(), 1)
		self.assertEqual(m.foo(), 2)
		with self.assertRaises(AssertionError):
			m.foo()


