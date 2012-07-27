from describe.flags import (NO_ARG, ANYTHING, is_flag, params_match)

class Invoke(object):
	"""A simple wrapper around a function that indicates the function should be invoked instead being
	treated as a value.
	"""
	def __init__(self, fn):
		self.fn = fn

	def __call__(self):
		return self.fn()

	def __repr__(self):
		return '<Invoke: %r>' % self.fn

class Expectation(object):
	"Handles the expectation for a given invocation / access."
	def __init__(self, attrname, returns=NO_ARG, args=ANYTHING, kwargs=ANYTHING):
		self.name, self.returns, self.args, self.kwargs = attrname, returns, args, kwargs

	@classmethod
	def raises(cls, attrname, error, args=ANYTHING, kwargs=ANYTHING):
		"An alternative constructor which raises the given error"
		def raise_error():
			raise error
		return cls(attrname, returns=Invoke(raise_error), args=ANYTHING, kwargs=ANYTHING)

	def satisfies_attrname(self, name):
		return self.name == name

	def satisfies_arguments(self, args, kwargs):
		return params_match(args, kwargs, self.args, self.kwargs)

	def return_value(self):
		if isinstance(self.returns, Invoke):
			return self.returns()
		return self.returns

	def is_consumed(self):
		return True

	def get_args_str(self):
		args = []
		if self.args and not is_flag(self.args):
			args += [repr(a) for a in self.args]
		if self.kwargs and not is_flag(self.kwargs):
			for k, v in self.kwargs.items():
				args.append('%s=%r' % (k, v))
		return args

	def __repr__(self):
		return '<Expect %(name)s(%(args)s) => %(returns)r>' % {
			'name': self.name,
			'returns': self.returns,
			'args': ', '.join(self.get_args_str()),
		}

class ExpectationList(object):
	"""Contains an object-level ordered list of expectations.

	The mock must be invoked in this given order.
	"""
	def __init__(self, *expectations):
		self.expects = list(expectations)
		self.history = []

	def add(self, *expectations):
		self.expects.extend(expectations)

	def _invoked(self, attrname, args, kwargs):
		print self.expects
		if not self.expects:
			raise AssertionError()
		expect = self.expects[0]
		if expect.satisfies_attrname(attrname):
			if expect.satisfies_arguments(args, kwargs):
				self.history.append(expect)
				try:
					result = expect.return_value()
				finally:
					if expect.is_consumed():
						self.expects.pop(0)
				print 'consumed', expect, '=>', result
				return result
			else:
				print 'failed satisfies_arguments'
		else:
			print 'failed satisfies_attrname', attrname
		raise AssertionError()

	def attribute_invoked(self, attrcatcher, args, kwargs):
		return self._invoked(attrcatcher._name_, args, kwargs)

	def attribute_read(self, attrcatcher, name):
		raise NotImplementedError("Invalid attr read")

	def key_read(self, attrcatcher, name):
		raise NotImplementedError("Invalid key access")

	def get_attribute(self, name):
		return self._invoked(name, (), {})

	@property
	def num_left(self):
		return len(self.expects)

	def __repr__(self):
		return "ExpectationList%r" % self.expects

class ExpectationSet(ExpectationList):
	"""Contains an object-level unordered list of expectations.

	The mock can be invoked in any order.
	"""
	def attribute_invoked(self, attrcatcher, args, kwargs):
		attrname = attrcatcher._name_
		for expect in self.expects:
			if expect.satisfies_attrname(attrname):
				if expect.satisfies_arguments(args, kwargs):
					self.history.append(expect)
					try:
						result = expect.return_value()
					finally:
						if expect.is_consumed():
							self.expects.remove(expect)
					return result
		raise AssertionError()

	def __repr__(self):
		return "ExpectationSet%r" % self.expects


class AttributeCatcher(object):
	"Simply captures values to pass to delegate."
	def __init__(self, name, delegate):
		self._name_, self._delegate_ = name, delegate

	def __call__(self, *args, **kwargs):
		return self._delegate_.attribute_invoked(self, args, kwargs)

	def __getitem__(self, key):
		return self._delegate_.key_read(self, key)

	def __getattribute__(self, name):
		if name in set(('__call__', '_delegate_', '_name_')):
			return super(AttributeCatcher, self).__getattribute__(name)
		return self._delegate_.attribute_read(self, name)


class ExpectationBuilder(object):
	def __init__(self, mock, attrname):
		self.mock, self.attrname = mock, attrname
		self.is_attr_read = True
		self.args = NO_ARG
		self.kwargs = NO_ARG

	def __call__(self, *args, **kwargs):
		if not self.is_attr_read:
			raise AssertionError("Cannot invoke multiple times!")
		self.is_attr_read = False
		self.args = args
		self.kwargs = kwargs
		return self

	def __expect(self, constructor, value):
		if not self.is_attr_read:
			self.mock.__invocations__.update([self.attrname])
		self.mock.__expectations__.add(constructor(self.attrname, value, args=self.args, kwargs=self.kwargs))

	def to_raise(self, error):
		self.__expect(Expectation.raises, error)

	def to_return(self, value):
		self.__expect(Expectation, value)


class ExpectationBuilderFactory(object):
	def __init__(self, mock):
		self.mock = mock

	def attribute_invoked(self, attrcatcher, args, kwargs):
		return ExpectationBuilder(self.mock, '__call__')(*args, **kwargs)

	def attribute_read(self, attrcatcher, name):
		return ExpectationBuilder(self.mock, name)

	def key_read(self, attrcatcher, name):
		return ExpectationBuilder(self.mock, '__getitem__')(name)

