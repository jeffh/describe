from describe.mock.utils import TWO_OPS_FULL, ONE_OPS, NIL
from describe.mock.expectations import Invoke, ExpectationList, ExpectationSet, Expectation
from describe.mock.mock import Mock
from describe.spec.utils import Replace


def stub(**attributes):
	delegate = StubErrorDelegate()
	m = Mock(name='Stub', error_delegate=delegate)
	delegate.instance = m
	for key, value in attributes.items():
		setattr(m, key, value)
	return m

def stub_attr(obj, key, value=NIL):
	if value is NIL:
		value = stub()
	return Replace(obj, key, value)

class StubErrorDelegate(object):
	def __init__(self):
		self.instance = None
		self.items = {}

	def _expectation_from_history(self, expectations, attrname, args, kwargs):
		recent_history = reversed(expectations.history)
		for expect in recent_history:
			try:
				return expectations.validate_expectation(expect, attrname, args, kwargs)
			except (ExpectationList.FailedToSatisfyArgumentsError, ExpectationList.FailedToSatisfyAttrnameError):
				pass
		raise IndexError()

	def no_expectations(self, expectations, attrname, args, kwargs):
		try:
			return self._expectation_from_history(expectations, attrname, args, kwargs)
		except IndexError:

			return self.instance

	def fails_to_satisfy_attrname(self, expectations, attrname, args, kwargs, expectation):
		s = stub()
		super(Mock, self.instance).__setattr__(attrname, s)
		return s

	def fails_to_satisfy_arguments(self, expectations, attrname, args, kwargs, expectation):
		s = stub()
		super(Mock, self.instance).__setattr__(attrname, s)
		return s

if 0:
	IGNORE_LIST = set((
	    '_Stub__attributes', '_Stub__magic', '_Stub__items', '__class__', '_create_magic_method',
	    # 'expects'
	))

	def process(dictionary, name, cls):
		if name not in dictionary:
			dictionary[name] = cls()
		if isinstance(dictionary[name], Invoke):
			return dictionary[name]()
		return dictionary[name]


	class Stub(object):
		"""Stubs are objects that can stand-in for any other object. It simply returns more stubs when
		accessed or invoked.

		This is used for testing functionality that doesn't particularly care about the objects they
		are manipulating, (ie - a function that splits an array in half doesn't care about what kinds
		                   of elements are in there)
		"""
		def __init__(self, **attributes):
			self.__attributes = attributes
			self.__items = {}
			self.__magic = {}

		@classmethod
		def attr(cls, obj, name, value=NIL):
			return StubAttr(obj, name, getattr(obj, name, NIL), value).replace()

		# @property
		# def expects(self):
		# 	raise TypeError('reserved for API')

		def __getattribute__(self, name):
			if name in IGNORE_LIST:
				return super(Stub, self).__getattribute__(name)
			return process(self.__attributes, name, self.__class__)

		def __setattr__(self, name, value):
			if name in IGNORE_LIST:
				return super(Stub, self).__setattr__(name, value)
			self.__attributes[name] = value

		def __getitem__(self, name):
			return self.__items.get(name, None)

		def __setitem__(self, name, value):
			self.__items[name] = value

		def __call__(self, *args, **kwargs):
			full_name = '__call__'
			return process(self.__magic, full_name, self.__class__)

		def _create_magic_method(name):
			full_name = '__%s__' % name
			def getter(self):
				return process(self.__magic, full_name, self.__class__)
			getter.__name__ = full_name
			return property(getter)

		for op in TWO_OPS_FULL + ONE_OPS:
			exec('__%s__ = _create_magic_method(%r)' % (op, op))


	class StubAttr(object):
		"Manages the lifetime of a stub on an attribute."
		def __init__(self, obj, name, orig_value, new_value):
			self.obj, self.name, self.orig_value, self.new_value = obj, name, orig_value, new_value

		@property
		def stub(self):
			return self.new_value

		def replace(self):
			if self.new_value is NIL:
				self.new_value = Stub()
			setattr(self.obj, self.name, self.new_value)
			return self

		def restore(self):
			if self.orig_value is NIL:
				delattr(self.obj, self.name)
			else:
				setattr(self.obj, self.name, self.orig_value)
			return self

		def __enter__(self):
			return self.replace().stub

		def __exit__(self, type, info, tb):
			self.restore()

		def __del__(self):
			self.restore()

