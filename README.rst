############
Describe
############

A `Behavior Driven Development`_ or BDD framework inspired off of RSpec_, Jasmine_, Dingus_ and Mote_.

It is worth noting the `development version`_ breaks the existing API.

.. _Behavior Driven Development: http://en.wikipedia.org/wiki/Behavior_Driven_Development
.. _BDD: http://en.wikipedia.org/wiki/Behavior_Driven_Development
.. _RSpec: http://rspec.info/
.. _Jasmine: http://pivotal.github.com/jasmine/
.. _Mote: https://github.com/garybernhardt/mote
.. _Dingus: https://github.com/garybernhardt/dingus
.. _development version: https://github.com/jeffh/describe/tarball/dev#egg=describe-dev

*************
Installation
*************

To install, use pip_ or easy_install_::

    pip install describe

Or use the latest `development version`_::

    pip install describe==dev

Then you can import it::

  from describe import Mock, stub, expect, verify_mock  # Primary features
  from describe import flags                            # Argument matching
  from describe import with_metadata                    # Minor feature

.. _pip: http://www.pip-installer.org/en/latest/index.html
.. _easy_install: http://peak.telecommunity.com/DevCenter/EasyInstall

*****
Usage
*****

Quickstart
==========

The core of describe is the expect object. In previous version, it was known as the Value object::

    from describe import expect

Use this Value class to wrap values you want to set expectations. Here's some API
examples until I get proper documentation::

    # self.assertEquals(9, 9)
    expect(9) == 9

    # self.assertAlmostEqual(5.0-4.0, 1.0)
    expect(5.0 - 4.0).to.be_close_to(1.0)

    # self.assertIn(3, (2,3,4))
    expect((2,3,4)).to.contain(3)

    # self.assertNotIn(5, (2,3,4))
    expect((2,3,4)).to_not.contain(5)

    # self.assertFalse(False)
    expect(False).to.be_falsy()

    # self.assertTrue(isinstance((), tuple))
    expect(()).to.be_an_instance_of(tuple)

    # self.assertGreaterEqual(5, 4)
    expect(5) >= 4

    # with self.assertRaisesRegexp(TypeError, 'foobar'):
    #     raise TypeError('foobar')
    with expect.to_raise_error(TypeError('foobar')):
        raise TypeError('foobar')

Mocks and Stubs (Doubles)
===============

Mocks and stubs are used to abstract out classes that are not being tested.
They can customized to return specific values to verify the target's class
interaction with other classes.

Besides construction, both Mocks and stubs are mostly identical. The only
exception is that Mocks can be asserted to verify the series of calls and
invocations on it are as expected.

Mocks are created using the `Mock` class::

    from describe import Mock
    m = Mock()

Mock supports the following arguments:

- ``name`` - The name of the mock when using repr. Purely for debugging.
- ``instance_of`` - The class this instance should be a subclass of, this
  allows it to pass isinstance and issubclass tests.
- ``ordered`` - Whether expectations set on this mock should be ordered.
  Defaults to True

Stubs are created using the `stub` function::

    from describe import stub

Once imported, you can create stubs.  Unless otherwise changed, nearly all interactions
with a stub will return either the same stub instance or a new stub.

The simpliest example is to create a stub with no arguments::

    die = stub()
    die.roll() # new stub instance

You can create stubs with predefined attributes::

    die = stub(sides=6)
    die.sides # => 6

Or set them manually::

    die.sides = 8
    die.sides # => 8

Magic methods for stubs defer to their appropriate instance methods. So
settings methods works as intended::

    die = stub(__eq__=lambda s: True)
    die == None # => True
    die == 2 # => True

But there's another way to customize methods we'll see below.

Since stub utilizes some magic methods for its all its work, the following
should not be overridden:

- ``__repr__``
- ``__getattr__``
- ``__init__``


Stubbing Attributes
-------------------

For shorthand, there's an ``stub_attr`` function which will stub out an
attribute of a given object and restore it after the with block ends::

    myobj.myattr = 4
    with stub_attr(myobj, 'myattr'):
        myobj.myattr # => stub returned
    myobj.myattr # => returns 4


Setting Expectations
--------------------

We can customize methods we expect, with return values and parameters.
This is done using the ``expects`` property::

    die = stub()
    stub.expects.roll().and_returns(6)
    die.roll() # => 6

The ``expects`` property can do index access and invocation::

    die = stub().expects[4].and_returns(2)
    die[4] # => 2
    die.expects('fizz').and_returns('buzz')
    die('fizz') # => 'buzz'

Or raise exceptions::

    die.expects.roll().and_raises(TypeError)
    die.roll() # => raises TypeError

Unlike stubs, Mocks will raise errors if expectations are not set before
they are invoked::

    m = Mock()
    m.foo() # raises AssertionError
    m.expects.foo().and_returns(2)
    m.foo() # => 2

Argument Filtering Expectation
------------------------------

It is also possible to expect types of incoming values::

    from describe import flags

    die = stub()
    die.expects.roll(flags.ANY_ARG).and_returns(3)
    die.roll(1) # => 3
    die.roll(2) # => 3
    die.roll(1, 2) # => stub instance

This is particularly useful for matching variable arguments or keyword arguments::

    from describe import flags

    die = stub()
    die.expects.roll(flags.ANY_ARGS, flags.ANY_KWARGS).and_returns(3)
    die.roll(3, 4, 5, 6) # => 3
    die.roll(foo='bar') # => 3
    die.roll('the cake', is_a='lie') # => 3

Or use ANYTHING as shorthand for ANY_ARGS and ANY_KWARGS::

    # both lines are equivalent
    die.expects.roll(flags.ANY_ARGS, flags.ANY_KWARGS).and_returns(3)
    die.expects.roll(flags.ANYTHING).and_returns(3)


Magic methods
---------------

Most magic methods are return stubs, similar to the behavior of Dingus_. You can
directly access these magic method stubs::

    die = stub()
    die.expects.__eq__(2).and_returns(True)
    die.expects.__eq__(1).and_returns(False)
    die == 2 # => True
    die == 1 # => False

The only notable exception are type-specific magic methods, such as
`__int__` and `__long__`.


Returning the Favor
-------------------

Expectations can be stacked. The last expectation is returned if no others are
available::

    die.expects.roll().and_returns(2)
    die.expects.roll().and_returns(3)
    die.roll() # => 2
    die.roll() # => 3
    die.roll() # => 3


The ``and_returns`` accepts any number of arguments, returning the given values it was
provided. It repeats the last value indefinitely::

    die = stub().expects.foo().and_return(1, 2, 3)
    die.foo() # => 1
    die.foo() # => 2
    die.foo() # => 3
    die.foo() # => 3
    # ...

In similar syntax, there are 3 other similar methods for telling the stub how to return
values:

* ``and_yields(*values)`` - returns a generator, yielding to each value provided.
* ``and_calls(*functions)`` - returns the value returned by calling each function. The functions
    accept the same arguments as if they received the call directly.
* ``and_raises(*errors)`` - raises each error given.

Except for ``and_yields``, all methods repeat the last value given to it.


Convenience Methods
-------------------

In many scenarios, you need to patch objects from existing libraries. This can
be prone to error, as you need to ensure restoration after the spec runs. For
convenience, Describe provides a set of functions to monkey-patch existing
objects: returning Stub instead of their normal value.

Patching is similar to Mock_ in design.

All patching is done from the patch object::

    from describe import patch

For example, we can patch standard out::

    # nothing actually goes to console
    with patch('sys.stdout'):
        print "hello world"

patch returns the Stub instance of the patched object, which you can use::

    with patch('os.getcwd') as getcwd:
        import os
        getcwd().expects().and_returns('foo')
        expect(os.getcwd()) == 'foo'

Alternatively, you can pass any value for the patch to replace with, instead of the
a stub instance::

    with patch('os.getcwd', lambda: 'lol'):
        import os
        expect(os.getcwd()) == 'lol'

If we're defining a function (see Specs section), we can use it as a decorator, the decorator
will pass the stub instance as the wrapped function's first argument::

    @patch('os.getcwd')
    def it_is_patched(getcwd):
        import os
        getcwd().expects().and_returns('foo')
        expect(os.getcwd()) == 'foo'

If the module exists in the namespace already, you can patch an attribute by it's object::

    import os
    @patch.object(os, 'getcwd')
    def it_is_also_patched(getcwd):
        getcwd().expects().and_returns('foo')
        expect(os.getcwd()) == 'foo'

Like Mock_, temporarily mutating a dictionary-like object is also possible::

    import os
    @patch.dict(os.environ, {'foo': 'bar'})
    def it_replaces_dict():
        expect(os.environ) == {'foo': 'bar'}


.. _Mock: http://www.voidspace.org.uk/python/mock/patch.html
.. _Mote: https://github.com/garybernhardt/mote

Advanced Mocks
==============

Some advanced techniques to use mocks. Some of these are currently using
internal APIs, so it's generally not recommended to use custom implementations.

Mocks actually support two extra arguments:

- ``error_delegate`` - A special object that is delegated to for when an
  AssertionError is normally raised. This allows you to do custom behaviors.
  Mocks use `describe.mock.MockErrorDelegate` which raises AssertionErrors.
  Stubs internally use `describe.mock.StubErrorDelegate` which returns a new
  stub per attribute.
- ``expectations`` - A custom internal expectation store for the given mock.
  Using a custom object here can provide custom expectation handling logic.
  The ``order`` argument makes the mock dispatch to either
  `describe.mock.expectations.ExpectationList` or 
  `describe.mock.expectations.ExpectationSet` respectively when the default
  value of `None` is provided for this argument.

For example, you can use a custom error_delegate to return stubs only
when no all expectations are already satisfied::

    from describe import stub

    # Arguments:
    #   expectations are the current list of expectations that were checked against
    #      (same as the `expectations` argument to mock)
    #   sender is the mock object being acted upon
    #   attrname is the attribute name the mock was being accesessed
    #   args is a tuple of the arguments called with
    #   kwargs is a dict of the arguments called with
    #   expectation is the expectation that caused the failure, if available
    #   the return value is what the mock should return to the caller

    class WeakerMockErrorDelegate(object):
        # this gets call when there are no more expectations to check
        def no_expectations(self, expectations, sender, attrname, args, kwargs):
            return stub()

        # this gets called when the expectation(s) fail to match the given attribute name
        def fails_to_satisfy_attrname(self, expectations, sender, attrname, args, kwargs, expectation):
            raise AssertionError('This mock does not have expectations for attribute: %r' % attrname)

        # this gets called when the expectation(s) fail to match the given arguments
        def fails_to_satisfy_arguments(self, expectations, sender, attrname, args, kwargs, expectation):
            raise AssertionError('This mock does not have expectations for: %s(%s)' % (attrname, get_args_str(args, kwargs)))

Although creating custom objects that supports the methods that
``expectations`` requires, you can reuse existing ExpectationLists to ensure
global ordering::

    # build a shared expectation list
    expectations = ExpectationList(delegate=MockErrorDelegate())
    # create mocks
    m1 = Mock(expectations=expectations)
    m2 = Mock(expectations=expectations)
    # generate expectation order
    m1.expects.foo().and_returns(1)
    m2.expects.foo().and_returns(2)

    # this blows up
    m2.foo() # => AssertionError
    # this works
    m1.foo() # => 1
    m2.foo() # => 2


Specs
=====

Of course, where are we defining these? In spec files of course! Currently describe
comes with one command, aptly named 'describe'. It simply runs all specs it can find
from the current working directory.

The describe command makes no assumptions on where the spec files. It simply looks for
spec files that end in '_spec.py'.

The simpliest example is to compare to how python's unittest_ library does it::

    # unittest
    from unittest import TestCase
    class DescribeCake(TestCase):
        def setUp(self):
            # before each test

        def tearDown(self):
            # after each test

        def test_it_should_be_tasty(self):
            # assertions for a test

    # describe
    class DescribeCake:
        def before_each(s, context):
            # before each example

        def after_each(s, context):
            # after each example

        def it_should_be_tasty(s, context):
            # test code

In addition to before_each and after_each, there is before_all and after_all if you
prefer to run code before and after the entire group / context is executed.

'Describe' definitions can be nested. Alternatively, the 'Context' prefix can
be used instead::

    # describe
    class DescribeCake:
        class ContextColor:
            def it_is_white(s, context):
                # test code

.. _unittest: http://docs.python.org/library/unittest.html

