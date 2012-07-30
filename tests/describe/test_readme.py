import sys
from cStringIO import StringIO
from unittest import TestCase

from describe import expect, patch, flags, Mock, stub

class DescribeSettingExpectations(TestCase):
    def test_it_accepts_any_arg(self):
        die = stub()
        die.expects.roll(flags.ANY_ARG).to_return(3)
        self.assertEqual(die.roll(1), 3)
        self.assertEqual(die.roll(2), 3)
        self.assertTrue(isinstance(die.roll(1, 2), Mock)) # => stub instance

    def test_it_accepts_variable_args_and_kwargs(self):
        die = stub()
        die.expects.roll(flags.ANY_ARGS, flags.ANY_KWARGS).to_return(3)
        self.assertEqual(die.roll(3, 4, 5, 6), 3)
        self.assertEqual(die.roll(foo='bar'), 3)
        self.assertEqual(die.roll('the cake', is_a='lie'), 3)

    def test_it_accepts_anything(self):
        die = stub()
        die.expects.roll(flags.ANYTHING).to_return(3)
        self.assertEqual(die.roll(3, 4, 5, 6), 3)
        self.assertEqual(die.roll(foo='bar'), 3)
        self.assertEqual(die.roll('the cake', is_a='lie'), 3)

# "Convenience Methods"
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
            getcwd.expects().to_return('foo')
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
            getcwd.expects().to_return('foo')
            expect(getcwd()) == 'foo'
            self.assertEqual(getcwd(), 'foo')
        is_patched()

    def test_it_patches_as_decorator_for_object(self):
        import os
        @patch.object(os, 'getcwd')
        def is_also_patched(getcwd):
            getcwd.expects().to_return('foo')
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


