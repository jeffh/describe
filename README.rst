Describe
========

A `Behavior Driven Development`_ or BDD framework inspired off of RSpec_, Jasmine_, Dingus_ and Mote_.

It is worth noting the `development version`_ breaks the existing API.

.. _Behavior Driven Development: http://en.wikipedia.org/wiki/Behavior_Driven_Development
.. _BDD: http://en.wikipedia.org/wiki/Behavior_Driven_Development
.. _RSpec: http://rspec.info/
.. _Jasmine: http://pivotal.github.com/jasmine/
.. _Mote: https://github.com/garybernhardt/mote
.. _Dingus: https://github.com/garybernhardt/dingus
.. _development version: https://github.com/jeffh/describe/tarball/dev#egg=describe-dev

Installation
-------------

To install, use pip_ or easy_install_::

    pip install describe

Or use the latest development version::

    pip install describe==dev

Then you can import it::

  from describe import stub, expect # API
  from describe import flags        # submodules

.. _pip: http://www.pip-installer.org/en/latest/index.html
.. _easy_install: http://peak.telecommunity.com/DevCenter/EasyInstall

Usage
=====

Quickstart
-----------

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

Mocks and Stubs
-----

Mocks are used to abstract out classes that are not being tested. They can customized to return
specific values to verify the target's class interaction with other classes. They are created
using the `stub` function::

    from describe import stub

Once imported, you can create stubs. The arguments provide to the stub are the attributes
of the created object::

    die = stub(sides=6)
    die.sides # => 6

You can pass assign functions and magic methods to these mocks, all these functions
accept self as the first argument::

    die = stub(roll=lambda s: 4, __eq__=lambda s: True)
    die.roll()  # => 4
    die == None # => True

Specs
-----

    from unittest import TestCase
    class TestCake(TestCase):
        def test_it_should_be_tasty(self):
            # test code

    def describe_cake():
        def before_each(self):
            self.cake =Cake()

        def describe_blue_cake():
            def before_each(self):
                self.cake.color = 'blue'

            def it_should_be_tasty(self):
                self.cake.foo()
                # test code
