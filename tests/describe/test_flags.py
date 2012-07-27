from unittest import TestCase
from mock import Mock

from describe import flags as f

class TestArgsMatch(TestCase):
	def test_it_matches_specific_args(self):
		self.assertTrue(f.args_match((3,), (3,)))
		self.assertFalse(f.args_match((3,), (2,)))

	def test_it_matches_anything(self):
		self.assertTrue(f.args_match((), f.ANYTHING))
		self.assertTrue(f.args_match((1, 2, 3), f.ANYTHING))
		self.assertTrue(f.args_match((1, 2), [f.ANYTHING]))

	def test_it_matches_any_args(self):
		self.assertTrue(f.args_match((), f.ANY_ARGS))
		self.assertTrue(f.args_match((1, 2, 3), f.ANY_ARGS))
		self.assertTrue(f.args_match((1, 2, 3), [f.ANY_ARGS]))

	def test_it_matches_any_arg(self):
		self.assertTrue(f.args_match((1,), [f.ANY_ARG]))
		self.assertFalse(f.args_match((), [f.ANY_ARG]))
		self.assertFalse(f.args_match((1, 2), [f.ANY_ARG]))

	def test_it_matches_no_arg(self):
		self.assertTrue(f.args_match((), f.NO_ARG))
		self.assertFalse(f.args_match((1,), f.NO_ARG))
		self.assertFalse(f.args_match((1, 2), f.NO_ARG))


	def test_it_matches_subclass(self):
		class Example(str):
			pass
		self.assertTrue(f.args_match((Example,), [f.Subclasses(str)]))
		self.assertFalse(f.args_match((int,), [f.Subclasses(str)]))

	def test_it_matches_instanceof(self):
		self.assertTrue(f.args_match(('foo',), [f.InstanceOf(str)]))
		self.assertFalse(f.args_match((1,), [f.InstanceOf(str)]))

	def test_it_matches_contains(self):
		self.assertTrue(f.args_match(([1, 2, 3],), [f.Contains(2)]))
		self.assertFalse(f.args_match(([1, 2, 3],), [f.Contains(4)]))
		self.assertFalse(f.args_match((1,), [f.Contains(str)]))

	def test_it_matches_included_pairs(self):
		self.assertTrue(f.args_match((dict(a=1, b=2, c=3),), [f.IncludesPairs(a=1, b=2)]))
		self.assertFalse(f.args_match((dict(a=1, b=2, c=3),), [f.IncludesPairs(a=2, b=2)]))
		self.assertFalse(f.args_match((None,), [f.IncludesPairs(a=2, b=2)]))
		self.assertFalse(f.args_match(([],), [f.IncludesPairs(a=2, b=2)]))

	def test_it_matches_callable(self):
		self.assertTrue(f.args_match((lambda: 1,), [f.Callable()]))
		self.assertFalse(f.args_match((1,), [f.Callable()]))

	def test_it_matches_length(self):
		self.assertTrue(f.args_match(([1, 2, 3],), [f.LengthOf(3)]))
		self.assertFalse(f.args_match((1,), [f.Callable()]))

class TestKwargsMatch(TestCase):
	def test_it_matches_specific_args(self):
		self.assertTrue(f.kwargs_match(dict(a=1, b=2), dict(a=1, b=2)))
		self.assertFalse(f.kwargs_match(dict(a=2, b=2), dict(a=1, b=2)))

	def test_it_matches_anything(self):
		self.assertTrue(f.kwargs_match({}, f.ANYTHING))
		self.assertTrue(f.kwargs_match(dict(a=1, b=2), f.ANYTHING))
		self.assertTrue(f.kwargs_match(dict(a=1, b=2), [f.ANYTHING]))

	def test_it_matches_any_kwargs(self):
		self.assertTrue(f.kwargs_match({}, f.ANY_KWARGS))
		self.assertTrue(f.kwargs_match(dict(a=1, b=2), f.ANY_KWARGS))
		self.assertTrue(f.kwargs_match(dict(a=1, b=2), [f.ANY_KWARGS]))

	def test_it_matches_any_arg(self):
		self.assertTrue(f.kwargs_match(dict(a=1), dict(a=f.ANY_ARG)))
		self.assertFalse(f.kwargs_match({}, dict(a=f.ANY_ARG)))
		self.assertFalse(f.kwargs_match(dict(a=1, b=2), dict(a=f.ANY_ARG)))

	def test_it_matches_dynamic_flags(self):
		valid_flag = Mock(spec=f.DynamicFlag)
		valid_flag.validate.return_value = True
		self.assertTrue(f.kwargs_match(dict(a=1), dict(a=valid_flag)))
		self.assertFalse(f.kwargs_match(dict(a=1, b=2), dict(a=valid_flag)))
		self.assertFalse(f.kwargs_match(dict(b=2), dict(a=valid_flag)))

		invalid_flag = Mock(spec=f.DynamicFlag)
		valid_flag.validate.return_value = False
		self.assertFalse(f.kwargs_match(dict(a=2), dict(a=valid_flag)))

