from unittest import TestCase

from mock import Mock, patch

from describe.mock.consumers import (ValueConsumer, ErrorConsumer,
        FunctionConsumer, IteratorConsumer)


class TestValueConsumer(TestCase):
    def test_value_consumer(self):
        vc = ValueConsumer([1, 2, 3])
        self.assertEqual(vc(), 1)
        self.assertEqual(vc(), 2)
        self.assertEqual(vc(), 3)

    def test_value_consumer_creates_copy(self):
        a = [1, 2, 3]
        vc = ValueConsumer(a)
        self.assertEqual(vc(), 1)
        self.assertEqual(vc(), 2)
        self.assertEqual(vc(), 3)
        self.assertEqual(len(a), 3)


class TestErrorConsumer(TestCase):
    def test_error_consumer(self):
        ec = ErrorConsumer([TypeError, ValueError('foo'), IOError])
        self.assertRaises(TypeError, ec)
        self.assertRaises(ValueError, ec)
        self.assertRaises(IOError, ec)
        self.assertRaises(IOError, ec)

    def test_error_raises_type_error_if_string(self):
        with self.assertRaises(TypeError):
            ec = ErrorConsumer(['foo'])


class TestIteratorConsumer(TestCase):
    def test_iterator_consumer(self):
        ic = IteratorConsumer([1, 2, 3])
        self.assertTrue(hasattr(ic(), 'next'))
        self.assertEqual(tuple(ic()), (1, 2, 3))


class TestFunctionConsumer(TestCase):
    def test_function_consumer(self):
        fc = FunctionConsumer([lambda: 1, lambda a, b: a + b, lambda a, b: a - b])
        self.assertEqual(fc(), 1)
        self.assertEqual(fc(1, 2), 3)
        self.assertEqual(fc(4, 2), 2)
