from unittest import TestCase

from describe.mock import stub, stub_attr, Invoke, Mock


# TODO: stub with a callable return? attr stub with callable??

class Foobar(object):
	def __init__(self, a, b, c):
		self.a, self.b, self.c = a, b, c

class TestStub(TestCase):
	def test_it_returns_stub_for_any_attributes(self):
		s = stub()
		self.assertTrue(isinstance(s.foo.bar.blah, Mock))

	def test_it_accepts_any_invocations(self):
		s = stub()
		self.assertEqual(s.foo(), s)
		self.assertEqual(s.bar(), s)

	def test_it_can_return_specified_values_for_attributes(self):
		s = stub(foo=2)
		s.bar = 4
		self.assertEqual(s.foo, 2)
		self.assertEqual(s.bar, 4)

	def test_it_can_receive_key_indicies(self):
		s = stub()
		self.assertEqual(s['foo'], s)
		s['bar'] = 34
		self.assertEqual(s['bar'], 34)

	def test_it_returns_stub_for_any_magic_methods(self):
		s = stub()
		self.assertTrue(isinstance(s + 2, Mock))

	def test_it_returns_value_from_callable(self):
		s = stub(foo=Invoke(lambda: 43))
		self.assertEqual(s.foo, 43)


class TestStubAttr(TestCase):
	def test_it_can_stub_an_attr_from_an_obj(self):
		o = Foobar(1, 2, 3)
		s = stub_attr(o, 'a')
		s.replace()
		self.assertIs(o.a, s.value)
		self.assertTrue(isinstance(s.value, Mock))
		s.restore()
		self.assertIsNot(o.a, s)

	def test_it_can_stub_an_attr_from_an_obj_using_with(self):
		o = Foobar(1, 2, 3)
		with stub_attr(o, 'a') as s:
			self.assertIs(o.a, s)
			self.assertTrue(isinstance(s, Mock))
		self.assertIsNot(o.a, s)
