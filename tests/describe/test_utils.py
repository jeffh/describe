import sys
from unittest import TestCase
from StringIO import StringIO

from mock import Mock

from describe.utils import Replace


class TestReplace(TestCase):
    def test_is_a_decorator(self):
        instance = Mock()
        state = {'count': 0}
        def foo(obj):
            "DocString"
            self.assertEqual(sys.stdout, instance)
            self.assertEqual(obj, instance)
            state['count'] += 1
            return 'foo'

        wrapped = Replace(sys, 'stdout', instance)(foo)
        wrapped()
        self.assertTrue(hasattr(wrapped, '__wraps__'))
        self.assertEqual(state['count'], 1)

    def test_replacement_of_attribute(self):
        import sys
        old = sys.stdout
        tmp = StringIO()
        with Replace(sys, 'stdout', tmp):
            self.assertNotEqual(old, sys.stdout)
            self.assertEqual(tmp, sys.stdout)
        self.assertNotEqual(tmp, sys.stdout)
        self.assertEqual(old, sys.stdout)

    def test_no_replacement_of_attribute_if_noop(self):
        import sys
        old = sys.stdout
        tmp = StringIO()
        with Replace(sys, 'stdout', tmp, noop=True):
            self.assertNotEqual(tmp, sys.stdout)
            self.assertEqual(old, sys.stdout)
        self.assertNotEqual(tmp, sys.stdout)
        self.assertEqual(old, sys.stdout)

