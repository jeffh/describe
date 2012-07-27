from describe.mock.utils import TWO_OPS_FULL, ONE_OPS, NIL
from describe.mock.expectations import Invoke, AttributeCatcher, Expectation, ExpectationBuilderFactory, ExpectationList, ExpectationSet


__all__ = ['Mock', 'verify_mock']


IGNORE_LIST = set((
    '__expectations__', '__invocations__', '__items__', 'expects', '__getitem__', '__initialize__',
    '__bases__', '__class__'
))

def process(expectations, invocations, name):
	if name in invocations:
		return AttributeCatcher(name, expectations)
	return expectations.get_attribute(name)

MAGIC_METHODS = ['getitem', 'setitem', 'call']

class Mock(object):
	"""Mocks are stricted cousins of Stub. Then raise AssertionErrors for any unexpected attribute accesses
	or method calls.

	Only pre-expected methods and attribute accesses are allowed, in the given order.
	"""
	def __init__(self, instance_of=None, ordered=True, expect_builder_factory=ExpectationBuilderFactory, attribute_catcher=AttributeCatcher):
		self.__initialize__ = dict(
		    expect_builder_factory=expect_builder_factory,
		    attribute_catcher=attribute_catcher,
		)
		if instance_of:
			self.__class__ = type('InstancedMock', (instance_of, Mock), {})
		if ordered:
			self.__expectations__ = ExpectationList()
		else:
			self.__expectations__ = ExpectationSet()
		self.__invocations__ = set(MAGIC_METHODS)

	@property
	def expects(self):
		attrcatcher_cls = self.__initialize__['attribute_catcher']
		expectation_builder_factory_cls = self.__initialize__['expect_builder_factory']
		return attrcatcher_cls(None, expectation_builder_factory_cls(self))

	def __getattribute__(self, name):
		if name in IGNORE_LIST:
			return super(Mock, self).__getattribute__(name)
		return process(self.__expectations__, self.__invocations__, name)

	def __setattr__(self, name, value):
		if name in IGNORE_LIST:
			return super(Mock, self).__setattr__(name, value)
		process(self.__expectations__, self.__invocations__, '__setattr__')(name, value)

	def _create_magic(name):
		full_name = '__%s__' % name
		def getter(self):
			return process(self.__expectations__, self.__invocations__, full_name)
		return property(getter)

	for op in TWO_OPS_FULL + ONE_OPS + MAGIC_METHODS:
		exec('__%s__ = _create_magic(%r)' % (op, op))


def verify_mock(m):
	"""Verifies that all mock expectations were called.
	"""
	assert m.__expectations__.num_left == 0


