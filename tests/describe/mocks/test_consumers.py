from unittest import TestCase

from mock import Mock, patch

from describe.mock.consumers import (ValueConsumer, ErrorConsumer,
        FunctionConsumer, IteratorConsumer, ChainedConsumer)


class TestChainedConsumer(TestCase):
    def test_it_validates_its_consumers(self):
        with self.assertRaises(TypeError):
            ChainedConsumer([None])

    def test_it_uses_consumers(self):
        values = [1, 2]
        c1, c2 = Mock(side_effect=lambda: values.pop(0)), Mock(return_value=3)
        c1.is_repeating.side_effect = lambda: not len(values)

        cc = ChainedConsumer([c1, c2])
        self.assertEqual(cc(), 1)
        self.assertEqual(cc(), 2)
        self.assertEqual(cc(), 3)

    def test_it_is_at_end(self):
        values1 = [1, 2]
        values2 = [3]
        c1, c2 = Mock(side_effect=lambda: values1.pop(0)), Mock(side_effect=lambda: values2.pop(0))
        c1.is_repeating.side_effect = lambda: not len(values1)
        c2.is_repeating.side_effect = lambda: not len(values2)
        c1.is_at_end.side_effect = lambda: len(values2) <= 1
        c2.is_at_end.side_effect = lambda: len(values2) <= 1

        cc = ChainedConsumer([c1, c2])
        self.assertFalse(cc.is_at_end())
        cc()
        self.assertFalse(cc.is_at_end())
        cc()
        self.assertTrue(cc.is_at_end())

    def test_it_is_repeating(self):
        values1 = [1, 2]
        values2 = [3]
        c1, c2 = Mock(side_effect=lambda: values1.pop(0)), Mock(side_effect=lambda: values2.pop(0))
        c1.is_repeating.side_effect = lambda: not len(values1)
        c2.is_repeating.side_effect = lambda: not len(values2)
        c1.is_at_end.side_effect = lambda: len(values1) <= 1
        c2.is_at_end.side_effect = lambda: len(values2) <= 1

        cc = ChainedConsumer([c1, c2])
        self.assertFalse(cc.is_repeating())
        cc()
        self.assertFalse(cc.is_repeating())
        cc()
        self.assertFalse(cc.is_repeating())
        cc()
        self.assertTrue(cc.is_repeating())

    def test_it_is_last_consumer_if_empty(self):
        cc = ChainedConsumer([])
        self.assertTrue(cc.is_at_end())

    def test_it_is_repeating_consumer_if_only_one(self):
        cc = ChainedConsumer([Mock()])
        self.assertTrue(cc.is_repeating_consumer())


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

    def test_is_at_end(self):
        vc = ValueConsumer([1, 2, 3])
        self.assertFalse(vc.is_at_end())
        vc(), vc()
        self.assertTrue(vc.is_at_end())

    def test_it_at_end_if_empty(self):
        vc = ValueConsumer([])
        self.assertTrue(vc.is_at_end())

    def test_is_repeating(self):
        vc = ValueConsumer([1, 2, 3])
        vc(), vc()
        self.assertFalse(vc.is_repeating())
        vc()
        self.assertTrue(vc.is_repeating())


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
