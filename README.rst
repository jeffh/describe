Describe
========

An experimental BDD_ styled framework inspired off of RSpec. The reason of BDD over
TDD is out of scope of this article. But this framework is simply a way to try and
encourage me to do more testing.

.. _BDD: http://en.wikipedia.org/wiki/Behavior_Driven_Development
.. _RSpec: http://rspec.info/

Installation
-------------

As of now, it is not on pip/easy_install (soon!).

Usage
-----

Then you can import the library for use in unittest or nose. Currently there is only
one feature, the Value object::

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


But this is more code!
======================

Yes, but it's more readable (your opinion may vary).