from unittest import TestCase

from describe.mock.utils import is_function


class TestIsFunction(TestCase):
    def test_function(self):
        self.assertTrue(is_function(lambda: 0))
        def lol():
            pass
        self.assertTrue(is_function(lol))

    def test_class(self):
        class Foo(object):
            pass
        self.assertFalse(is_function(object))
        self.assertFalse(is_function(Foo))
        self.assertFalse(is_function(type))
