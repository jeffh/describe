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

  from describe import Mock, stub, expect  # Primary features
  from describe import flags               # Argument matching
  from describe import with_metadata       # Minor feature

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

**Warning, stubs are in a refactor phase**

Mocks are used to abstract out classes that are not being tested. They can customized to return
specific values to verify the target's class interaction with other classes.

Currently, describe makes no distinction between Mocks and Stubs.

They are created using the `stub` function::

    from describe import stub

Once imported, you can create stubs.  Unless otherwise changed, nearly all interactions
with a stub will return either the same stub instance or a new stub.

The simpliest example is to create a stub with no arguments::

    die = stub()
    die.roll()

You can create stubs with predefined attributes::

    die = stub(sides=6)
    die.sides # => 6

You can use the ``with_class_attrs`` to override magic methods. This is useful if you only
want to quickly change the way the stub responds to a magic method. Remember that functions
given must accept self::

    die = stub().with_class_attrs(__eq__=lambda s: True)
    die.roll()  # => 4
    die == None # => True

But there are better ways to customize the behavior of most magic methods.


Stubbing Attributes
-------------------

For shorthand, there's an ``attr`` class method with will stub out an attribute of a given
object and restore it when ``verify_expectations`` is called::

    myobj.myattr = 3
    stub = stub.attr(myobj, 'myattr')
    myobj.myattr # => stub returned by Stub.attr
    stub.verify_expectations()
    myobj.myattr # => 3


Setting Expectations
--------------------

Mocks expect a specific set of interactions to take place. We can do this using the
``expects`` property::

    die = stub()
    stub.expects.roll().and_returns(6)
    die.roll() # => 6
    die.verify_expectations() # noop

Here, the stub expects the roll method to be called. The verify_expectations method performs
the assertion that roll was indeed called. If not, an assertion is raised::

    # methods prefixed with 'and_' return the stub.
    die = stub().expects.roll().and_returns(6)
    die.verify_expectations() # raises AssertionError

The ``expects`` property can do index access and invocation::

    die = stub().expects[4].and_returns(2)
    die[4] # => 2
    die.expects('fizz').and_returns('buzz')
    die('fizz') # => 'buzz'

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
    die.__eq__.expects(2).and_returns(True)
    die.__eq__.expects(1).and_returns(False)
    die == 2 # => True
    die == 1 # => False

The only notable exception are type-specific magic methods, such as
`__int__` and `__long__`.


Returning the Favor
-------------------

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


Counting Expectations
---------------------

Prior to any of the ``and_`` methods, you can also use a quantifier, indicating how many
times the given method should be called. By default, all expectations set, assume that
they should be invoked at least once unless otherwise set like this::

    die = stub().expects.roll(2).at_least(2).and_returns(True)
    die.expects.roll(3).at_most(1).and_returns(True)
    die.expects.roll(4).exactly(3).and_returns(True)

    # ... use die ...

    die.verify_expectations()


Convenience Methods
-------------------

In many scenarios, you need to patch objects from existing libraries. This can be prone
to error, as you need to ensure restoration after the spec runs. For convenience,
Describe provides a set of functions to monkey-patch existing objects: returning
Stub instead of their normal value.

Patching is similar to Mock_ in design, but also with isolation patching offered in
Mote_.

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

