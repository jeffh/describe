import sys
from unittest import TestCase
from mock import Mock, patch

from describe.mock.patching import patch as patcher
from describe.mock.patching import DictReplacement
from describe.spec.utils import with_metadata
from describe.mock.stub import stub

import os.path


class DescribeDictReplacement(TestCase):
    def test_it_replaces_dictionary_contents(self):
        blah = {'a': 1, 'b': 2}
        with DictReplacement(blah, {'b': 3, 'c': 4}):
            self.assertEqual(blah, {'b': 3, 'c': 4})

    def test_it_can_be_a_decorator(self):
        state = {'count': 0}
        foo = {'a': 1, 'b': 2}
        def verify():
            state['count'] += 1
            self.assertEqual(foo, {'b': 3, 'c': 4})

        wrapped_verify = DictReplacement(foo, {'b': 3, 'c': 4})(verify)
        wrapped_verify()
        self.assertTrue(hasattr(wrapped_verify, '__wraps__'))
        self.assertEqual(state['count'], 1)


class DescribePatch(TestCase):
    def test_it_patches_dictionaries(self):
        foo = {'baz': 4}
        with patcher.dict(foo, {'bar': 1, 'baz': 3}):
            self.assertEqual(foo, {'bar': 1, 'baz': 3})
        self.assertEqual(foo, {'baz': 4})

    def test_it_temporarily_patches_other_namespaces(self):
        instance = Mock()
        self.assertNotEqual(sys.stdout, instance)

        with patcher('os.getcwd', instance) as path:
            import os
            self.assertEqual(os.getcwd, instance)
        self.assertNotEqual(os.getcwd, instance)

    def test_patching_manually(self):
        instance = Mock()
        self.assertNotEqual(sys.stdout, instance)

        p = patcher.object(sys, 'stdout', instance)
        p.start()
        self.assertEqual(sys.stdout, instance)
        p.stop()

        self.assertNotEqual(sys.stdout, instance)

    @patch('describe.mock.patching.stub')
    def test_it_temporarily_replaces_a_given_object_attr_with_stub(self, Stub):
        instance = Stub.return_value
        self.assertNotEqual(sys.stdout, instance)

        with patcher.object(sys, 'stdout') as stdout:
            self.assertEqual(stdout, instance)
            self.assertEqual(sys.stdout, instance)

        self.assertNotEqual(sys.stdout, instance)

    def test_it_can_be_used_as_a_descriptor(self):
        instance = Mock()
        self._called = 0

        @patcher.object(sys, 'stdout', instance)
        def foo(obj):
            "DocString"
            self.assertEqual(sys.stdout, instance)
            self.assertEqual(obj, instance)
            self._called = 1
            return 'foo'

        # check for some function attr preserved
        self.assertEqual(foo.__name__, 'foo')
        self.assertEqual(foo.__doc__, 'DocString')

        self.assertNotEqual(sys.stdout, instance) # no prepatching
        self.assertEqual(foo(), 'foo') # preserves return value
        self.assertNotEqual(sys.stdout, instance) # check restoration
        self.assertEqual(self._called, 1) # assert execution of original func


