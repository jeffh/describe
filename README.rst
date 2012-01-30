Describe
========

A `Behavior Driven Development`_ or BDD framework inspired off of RSpec_. The reason of BDD over
TDD is out of scope of this project. But this framework is simply a way to try and
encourage me to do more testing.

It is worth noting the `development version`_ breaks the existing API.

.. _Behavior Driven Development: http://en.wikipedia.org/wiki/Behavior_Driven_Development
.. _BDD: http://en.wikipedia.org/wiki/Behavior_Driven_Development
.. _RSpec: http://rspec.info/
.. _development version: https://github.com/jeffh/describe/tarball/dev#egg=describe-dev

Installation
-------------

To install, use pip or easy_install::

  pip install describe

Then you can import it::

  from describe import Spec, Value, Mock # classes
  from describe import arg, repository   # submodules

Usage
=====

Quickstart
-----------

Then you can import the library for use in unittest or nose. The core feature is the Value object::

  from describe import Value

Use this Value class to wrap values you want to set expectations. Here's some API
examples until I get proper documentation::

  # self.assertEquals(9, 9)
  Value(9).should == 9

  # self.assertAlmostEqual(5.0-4.0, 1.0)
  Value(5.0-4.0).should.be_close_to(1.0)

  # self.assertIn(3, (2,3,4))
  Value((2,3,4)).should.contain(3)

  # self.assertNotIn(5, (2,3,4))
  Value((2,3,4)).should_not.contain(5)

  # self.assertFalse(False)
  Value(False).should.be.false()

  # self.assertTrue(isinstance((), tuple))
  Value(()).should.be.instance_of(tuple)

  # self.assertEqual(len(range(5)), 5)
  # '.elements' is optional
  Value(range(5)).should.have(5).elements

  # self.assertGreaterEqual(len(range(5)), 4)
  Value(range(5)).should.have.at_least(4)

Mocks
-----

Mocks are used to abstract out classes that are not being tested. They can customized to return
specific results and logs all operations done to it for verification later on. The mock API wraps
the `voidspace mock library`_. Feel free to use it directly instead of this API.

describe.Mock supports a few operations:

* ``Mock.should_access property`` - Allows you to set expectations of method calls and attribute accesses.
* ``Mock.should_not_access(attr_name)`` - Allows you to set expections of attributes not getting accessed.
* ``Mock.verify()`` - Verifies all the expectations, throwing AssertionErrors if need be.
* ``Mock.reset_mock()`` - clears the access log, you should never really use this directly.

All other attributes get directed to the `voidspace mock object`_. A basic example::

   # create the mock
   from describe import Mock
   m = Mock()

   # set an expectation on what will be performed on the object and it's response
   m.should_access.upper().and_return('FOO')

   # run it
   m.upper() # => 'FOO'

   # verify that the operations were executed
   m.verify()

   # if you want to invoke any operations on the mock object (and not the API), get the
   # voidspace mock object via the mock attribute:
   m.should_access.verify().and_return('bar')
   m.mock.verify() # => 'bar'
   m.verify()

These expectations expect the function prototype you give it::

  m.should_access.rjust(5).and_return('     ')
  m.rjust()  # => None - prototype does not match.
  m.rjust(5) # => '     '
  m.verify() # will raise AssertionError because m.rjust() was called

Keyword arguments work just as well as args. There are several special arguments you can give
for special operations.

args.ANYTHING accepts any arguments as valid, including no arguments::

  from describe import args
  m.should_access.rjust(args.ANYTHING).and_return('anything works')
  m.rjust('foo', 'bar') # => 'anything works'

args.ANY_ARG accepts any single argument::

  from describe import args
  m.should_access.rjust(args.ANY_ARG).and_return(4)
  m.rjust() # => None - is not one argument
  m.rjust(3) # => 4

Other special args include:

* ``arg.ARGS``  - any non-keyword arguments
* ``arg.KWARGS`` - any keyworded arguments
* ``arg.an_instance_of(type)`` - any argument whos value matches the given type
* ``arg.regexp`` - alias for arg.an_instance_of(type(re.compile(''))) for a regular expression type.
* ``arg.includes_pair(key, value)`` - any argument who has a key and associated value.
* ``arg.contains(item, *items)`` - any keys or items in the given list or dictionary.
* ``arg.duck_type(*attributes)`` - any object that has all of the given attributes

You can also set expectations for getter properties::

  m.should_access.score.and_return(23)
  m.score # => 23

Calling verify on every mock object you create is tiresome. Fortunately, each mock is added to
a registry when instantiated. By default, they are added to the describe.mock.repository.default
repository. You can call verify() on the repository to verify all mocks in it::

  # create mocks:
  from describe import Mock, Value
  from describe.mock import repository
  for i in range(5):
    m = Mock()
    m.should_access.lower().and_return('bar')
    Value(m.lower()).should == 'bar'

  repository.default.verify() # will verify all mock objects we created above

.. _voidspace mock library: http://www.voidspace.org.uk/python/mock/
.. _voidspace mock object: http://www.voidspace.org.uk/python/mock/mock.html

Specs
-----

The entire purpose of behavior driven development, is to remap the testing-based terminology to
more specification driven ones. The Spec class is an alternative to unittest.TestCase, but you'll
need nose_ / sniffer_ to reap all the benefits.

Currently Specs inherit unittest.TestCase::

  from describe import Spec, Mock
  from describ.args import *
  class DescribeRSpecExpectingArguments(Spec):
      def before(self):
          self.m = Mock()

      def it_should_expect_arguments(self):
          self.m.should_access.msg(1,2,3)
          self.m.msg(1,2,3)

      def it_should_expect_arguments_with_count(self):
          self.m.should_access.msg(1,2,3).once
          self.m.msg(1,2,3)

      def it_should_expect_no_arguments(self):
          self.m.should_access.msg()
          self.m.msg()

      def it_should_expect_any_arguments(self):
          self.m.should_access.msg(ANYTHING)
          self.m.msg(1,2,3,4,5,6)

Then use the `SpecPlugin`` for nose to run the specs, or run describe.main program.

.. _nose: http://somethingaboutorange.com/mrl/projects/nose/1.0.0/
.. _sniffer: https://github.com/jeffh/sniffer
