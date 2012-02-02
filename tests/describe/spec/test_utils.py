from unittest import TestCase
from StringIO import StringIO
from functools import wraps

from mock import Mock, patch

from describe.spec.utils import tabulate, Replace, Benchmark, CallOnce, \
        getargspec, func_equal, accepts_arg, locals_from_function


class DescribeAcceptArgs(TestCase):
    def it_returns_True_for_function_with_one_arg(self):
        def foo(a):
            pass

        self.assertTrue(accepts_arg(foo))

    def it_returns_True_for_class_method_with_one_arg(self):
        class Foobar(object):
            def foo(self, a):
                pass

        self.assertTrue(accepts_arg(Foobar().foo))

    def it_returns_False_otherwise(self):
        class Foobar(object):
            def foo(self):
                pass

        def foo():
            pass

        self.assertFalse(accepts_arg(Foobar().foo))
        self.assertFalse(accepts_arg(foo))

    def it_returns_False_when_non_function(self):
        self.assertFalse(accepts_arg(None))


class DescribeIntegrationGetArgSpec(TestCase):
    def it_returns_argspec_of_functions(self):
        fn = lambda a: 0
        self.assertEqual(getargspec(fn), (('a',), None, None, None))

    def it_returns_argspec_of_class_constructor(self):
        class Foo(object):
            def __init__(self, f):
                pass
        self.assertEqual(getargspec(Foo), (('f',), None, None, None))

    def it_returns_argspec_of_class_call_magicmethod(self):
        class Foo(object):
            def __call__(self, f):
                pass
        self.assertEqual(getargspec(Foo), (('f',), None, None, None))

    def it_returns_argspec_of_wrapped_function(self):
        fn = wraps(lambda a: 0)
        self.assertEqual(getargspec(fn), (('a',), None, None, None))

    def it_returns_argspec_of_wrapped_function_with_CallOnce(self):
        fn = CallOnce(lambda a: 0)
        self.assertEqual(getargspec(fn), (('a',), None, None, None))


class DescribeCallOnce(TestCase):
    def test_it_can_call_wrapped_fn_once(self):
        m = Mock()
        subject = CallOnce(m)

        subject()
        subject()
        subject()

        m.assert_called_once_with()

    def test_it_does_nothing_for_wrapping_None(self):
        subject = CallOnce(None)
        subject()
        subject()

    def test_its_equal_with_None(self):
        subject = CallOnce(None)
        self.assertEqual(subject, CallOnce(None))

    def test_its_equal_with_like_function(self):
        subject = CallOnce(lambda:0)
        self.assertEqual(subject, CallOnce(lambda:0))

    def test_its_truthiness_if_wrapped_is_callable(self):
        subject = CallOnce(object())
        self.assertFalse(bool(subject))

    def test_its_truthiness_if_wrapped_is_callable(self):
        subject = CallOnce(lambda:0)
        self.assertTrue(bool(subject))

    def test_it_preserves_function_attributes(self):
        m = Mock()
        m.__doc__ = 'my fn doc'
        m.__name__ = 'my_func'
        m.__module__ = 'super.awesome.module'
        m.func_name = 'my_fn'
        m.func_code = Mock()
        subject = CallOnce(m)
        self.assertEqual(subject.__doc__, 'my fn doc')
        self.assertEqual(subject.__name__, 'my_func')
        self.assertEqual(subject.__module__, 'super.awesome.module')
        self.assertEqual(subject.func_name, 'my_fn')
        self.assertEqual(subject.func_code, m.func_code)


class TestFuncEqual(TestCase):
    def test_it_compares_lambda_function_equality(self):
        self.assertTrue(func_equal(lambda:0, lambda:0))
        self.assertTrue(func_equal(lambda:1, lambda:1))
        self.assertFalse(func_equal(lambda:2, lambda:1))

    def test_it_compares_function_equality(self):
        def add(a, b): return a + b
        def new_add(a, b): return a + b
        def sub(a, b): return a - b
        def sub_const(a): return a - 2
        self.assertTrue(func_equal(add, new_add))
        self.assertFalse(func_equal(new_add, sub))
        self.assertFalse(func_equal(sub, sub_const))

    @patch('describe.spec.utils.get_true_function')
    def test_it_compares_class_constructors(self, getfn):
        getfn.side_effect = lambda o: (o.__init__, None)
        class Foo(object):
            def __init__(self, bar):
                self.bar = bar
        class FooBar(object):
            def __init__(self, cake):
                self.bar = cake
        class ABC(object):
            def __init__(self, cake, bar):
                self.cake = cake
                self.bar()
        class Cake(object):
            def __init__(self, roflcopter, empty):
                self.bake = roflcopter

        self.assertTrue(func_equal(Foo, FooBar))
        print 'equal'
        self.assertFalse(func_equal(Foo, ABC))
        self.assertFalse(func_equal(Foo, Cake))

    @patch('describe.spec.utils.get_true_function')
    def test_it_compares_callables(self, getfn):
        getfn.side_effect = lambda o: (o.__call__, None)
        class Foo(object):
            def __call__(self, a, b):
                return a + b
        class FooBar(object):
            def __call__(self, a, b):
                return a + self.b
        class Cake(object):
            def __call__(self, c, b):
                return c + b

        self.assertFalse(func_equal(Foo(), FooBar()))
        self.assertTrue(func_equal(Foo(), Cake()))


class TestTabulate(TestCase):
    def test_tabulation_of_string(self):
        self.assertEqual(tabulate('foo\nbar'), '    foo\n    bar')

    def test_tabulation_does_not_insert_spaces_between_double_newlines(self):
        self.assertEqual(tabulate('\n\nfoo'), '\n\n    foo')

    def test_tabulation_ignores_first_line(self):
        self.assertEqual(tabulate('foo\nbar', ignore_first=True), 'foo\n    bar')

    def test_tabulation_by_times(self):
        self.assertEqual(tabulate('\n\nfoo', times=2), '\n\n        foo')

    def test_tabulation_by_zero_times(self):
        self.assertEqual(tabulate('\n\nfoo', times=0), '\n\nfoo')


class TestLocalsFromFunction(TestCase):
    def test_extracts_local_functions_with_invocation(self):
        behavior = 0
        def describe_spec():
            global behavior
            lol = True
            def it_should_read_submethods(): pass
            def before_each(): pass
            def before_all(): pass
            def sample_func(): pass
            def after_each(): pass
            def after_all(): pass
            def it_should_capture_this_method(): pass
            behavior += 1

        context = locals_from_function(describe_spec)
        methods = [
            'it_should_read_submethods',
            'before_each',
            'before_all',
            'after_each',
            'after_all',
            'it_should_capture_this_method',
            'sample_func',
        ]
        self.assertEqual(set(context.keys()), set(methods))
        self.assertEqual(behavior, 0)


class TestReplace(TestCase):
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

class TestBenchmark(TestCase):
    def test_benchmark(self):
        import time
        timer = Benchmark()
        with timer:
            time.sleep(0.1)
        self.assertTrue(timer.history[-1] > 0.09)

    def test_benchmark_multiple(self):
        import time
        timer = Benchmark()
        with timer: time.sleep(0.02)
        with timer: time.sleep(0.02)
        with timer: time.sleep(0.02)
        with timer: time.sleep(0.02)
        with timer: time.sleep(0.02)
        self.assertEqual(len(timer.history), 5)
        self.assertTrue(timer.total_time > 0.09)


