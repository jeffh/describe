from unittest import TestCase
from mock import Mock, patch

from describe.mock import Stub, Invoke


# TODO: stub with a callable return? attr stub with callable??

class Foobar(object):
	def __init__(self, a, b, c):
		self.a, self.b, self.c = a, b, c

class TestStub(TestCase):
	def test_it_returns_stub_for_any_attributes(self):
		s = Stub()
		self.assertTrue(isinstance(s.foo.bar.blah, Stub))

	def test_it_accepts_any_invocations(self):
		s = Stub()
		self.assertEqual(s.foo(), None)
		self.assertEqual(s.bar(), None)

	def test_it_can_return_specified_values_for_attributes(self):
		s = Stub(foo=2)
		s.bar = 4
		self.assertEqual(s.foo, 2)
		self.assertEqual(s.bar, 4)

	def test_it_can_receive_key_indicies(self):
		s = Stub()
		self.assertEqual(s['foo'], None)
		s['bar'] = 34
		self.assertEqual(s['bar'], 34)

	def test_it_returns_stub_for_any_magic_methods(self):
		s = Stub()
		self.assertEqual(s + 2, Stub)

	def test_it_returns_value_from_callable(self):
		s = Stub(foo=Invoke(lambda: 43))
		self.assertEqual(s.foo, 43)


class TestStubAttr(TestCase):
	def test_it_can_stub_an_attr_from_an_obj(self):
		o = Foobar(1, 2, 3)
		s = Stub.attr(o, 'a')
		self.assertIs(o.a, s.stub)
		self.assertTrue(isinstance(s.stub, Stub))
		s.restore()
		self.assertIsNot(o.a, s)

	def test_it_can_stub_an_attr_from_an_obj_using_with(self):
		o = Foobar(1, 2, 3)
		with Stub.attr(o, 'a') as s:
			self.assertIs(o.a, s)
			self.assertTrue(isinstance(s, Stub))
		self.assertIsNot(o.a, s)
