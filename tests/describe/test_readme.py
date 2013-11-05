import sys
from cStringIO import StringIO
from unittest import TestCase

from describe import expect, patch, flags, Mock, stub

class DescribeSettingExpectations(TestCase):
    def test_it_accepts_any_arg(self):
        die = stub()
        die.expects.roll(flags.ANY_ARG).and_returns(3)
        self.assertEqual(die.roll(1), 3)
        self.assertEqual(die.roll(2), 3)
        self.assertTrue(isinstance(die.roll(1, 2), Mock)) # => stub instance

    def test_it_accepts_variable_args_and_kwargs(self):
        die = stub()
        die.expects.roll(flags.ANY_ARGS, flags.ANY_KWARGS).and_returns(3)
        self.assertEqual(die.roll(3, 4, 5, 6), 3)
        self.assertEqual(die.roll(foo='bar'), 3)
        self.assertEqual(die.roll('the cake', is_a='lie'), 3)

    def test_it_accepts_anything(self):
        die = stub()
        die.expects.roll(flags.ANYTHING).and_returns(3)
        self.assertEqual(die.roll(3, 4, 5, 6), 3)
        self.assertEqual(die.roll(foo='bar'), 3)
        self.assertEqual(die.roll('the cake', is_a='lie'), 3)

class DescribeMagicMethods(TestCase):
    def test_custom_equality(self):
        die = stub()
        die.expects.__eq__(2).and_returns(True)
        die.expects.__eq__(1).and_returns(False)
        self.assertEqual(die, 2)
        self.assertNotEqual(die, 1)

class DescribeReturningTheFavor(TestCase):
    def test_it_supports_multiple_returns(self):
        die = stub()
        die.expects.roll().and_returns(2)
        die.expects.roll().and_returns(3)
        self.assertEqual(die(), 2)
        self.assertEqual(die(), 3)
        self.assertEqual(die(), 3)

    def test_it_supports_multiple_returns_inlined(self):
        die = stub()
        die.expects.roll().and_returns(2, 3)
        self.assertEqual(die(), 2)
        self.assertEqual(die(), 3)
        self.assertEqual(die(), 3)

    def test_it_supports_yielding(self):
        die = stub()
        die.expects.roll().and_yields(2, 3)
        self.assertEqual(list(die.roll()), [2, 3])

    def test_it_supports_functions(self):
        die = stub()
        die.expects.roll().and_calls(lambda x: 1, lambda x: x)
        self.assertEqual(die.roll(6), 1)
        self.assertEqual(die.roll(6), 6)
        self.assertEqual(die.roll(5), 5)

    def test_it_supports_exceptions(self):
        die = stub()
        die.expects.roll().and_raises(TypeError)
        with self.assertRaises(TypeError):
            die.roll()
        with self.assertRaises(TypeError):
            die.roll()

class DescribeConvenienceMethods(TestCase):
    def test_it_patches_stdout_using_with(self):
        # nothing actually goes to console
        old = sys.stdout
        buf = sys.stdout = StringIO()
        try:
            with patch('sys.stdout'):
                print "hello world"
        finally:
            sys.stdout = old
        self.assertEquals(buf.getvalue(), "")

    def test_it_patches_using_with_plus_arg(self):
        # nothing actually goes to console
        with patch('os.getcwd') as getcwd:
            import os
            getcwd.expects().and_returns('foo')
            expect(os.getcwd()) == 'foo'
            self.assertEqual(os.getcwd(), 'foo')

    def test_it_patches_using_alternative_value(self):
        with patch('os.getcwd', lambda: 'lol'):
            import os
            expect(os.getcwd()) == 'lol'
            self.assertEqual(os.getcwd(), 'lol')

    def test_it_patches_as_decorator(self):
        @patch('os.getcwd')
        def is_patched(getcwd):
            import os
            getcwd.expects().and_returns('foo')
            expect(getcwd()) == 'foo'
            self.assertEqual(getcwd(), 'foo')
        is_patched()

    def test_it_patches_as_decorator_for_object(self):
        import os
        @patch.object(os, 'getcwd')
        def is_also_patched(getcwd):
            getcwd.expects().and_returns('foo')
            self.assertEqual(os.getcwd(), 'foo')
        is_also_patched()

    def test_it_replaces_dict(self):
        import os
        @patch.dict(os.environ, {'foo': 'bar'})
        def it_replaces_dict():
            expect(os.environ) == {'foo': 'bar'}
            self.assertEqual(os.environ, {'foo': 'bar'})

        it_replaces_dict()
        expect(os.environ) != {'foo': 'bar'}
        self.assertNotEqual(os.environ, {'foo': 'bar'})

