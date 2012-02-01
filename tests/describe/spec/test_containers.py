
from unittest import TestCase, TestSuite

from mock import Mock, MagicMock, patch

from describe.spec.containers import SpecFile, Example, ExampleGroup, \
        ExampleGroupTestSuite, Context, Failure


class DescribeFailure(TestCase):
    def test_it_should_have_equality(self):
        f1 = Failure(TypeError('foo'), 'foo', 'bar')
        f2 = Failure(TypeError('foo'), 'foo', 'bar')

        self.assertEqual(f1, f2)

    def test_it_should_be_not_equal_if_traceback_is_different(self):
        f1 = Failure(TypeError('foo'), 'bar')
        f2 = Failure(TypeError('foo'), 'foo')

        self.assertNotEqual(f1, f2)

    def test_it_should_be_not_equal_if_stdout_is_different(self):
        f1 = Failure(TypeError('foo'), 'bar', Mock())
        f2 = Failure(TypeError('foo'), 'bar', Mock())

        self.assertNotEqual(f1, f2)

    def test_it_should_be_not_equal_if_stderr_is_different(self):
        f1 = Failure(TypeError('foo'), 'bar', 'baz', Mock())
        f2 = Failure(TypeError('foo'), 'bar', 'baz', Mock())

        self.assertNotEqual(f1, f2)


class DescribeContext(TestCase):
    def test_it_should_accept_properties(self):
        c = Context()
        c.foo = 'bar'
        self.assertEqual(c.foo, 'bar')

    def test_it_should_accept_keys(self):
        c = Context()
        c['foo'] = 'bar'
        self.assertEqual(c['foo'], 'bar')

    def test_it_can_read_keys_from_parents(self):
        c = Context(parent=Context({'foo': 'bar'}))
        self.assertEqual(c['foo'], 'bar')

    def test_it_should_read_properties_from_parents(self):
        c = Context(parent=Context(properties={'foo': 'bar'}))
        self.assertEqual(c.foo, 'bar')


class DescribeExampleGroupTestSuite(TestCase):
    def test_it_can_run_before_all_and_after_all(self):
        before_all, after_all = Mock(), Mock()

        subject = ExampleGroupTestSuite([Mock()], before_all, after_all)
        subject.debug()

        before_all.assert_called_once_with()
        after_all.assert_called_once_with()


class DescribeExampleGroupAsList(TestCase):
    def setUp(self):
        self.test1 = Mock()
        self.test2 = Mock()
        self.test3 = Mock()
        self.subject = ExampleGroup(Mock(), Mock(), examples=[self.test1, self.test2, self.test3])

    def test_it_supports_iteration_of_examples(self):
        self.assertEqual(list(self.subject), [self.test1, self.test2, self.test3])

    def test_it_supports_len(self):
        self.assertEqual(len(self.subject), 3)

    def test_it_supports_append_and_getitem(self):
        t = Mock()
        self.subject.append(t)
        self.assertEqual(self.subject[-1], t)

    def test_it_supports_remove(self):
        self.subject.remove(self.test1)
        self.assertEqual(list(self.subject), [self.test2, self.test3])

    def test_it_contains_examples(self):
        self.assertIn(self.test2, self.subject.examples)
        self.assertIn(self.test3, self.subject.examples)


class DescribeExampleGroup(TestCase):
    @patch('describe.spec.containers.ExampleGroupTestSuite')
    def test_it_can_produce_testsuite(self, egte):
        instance = egte.return_value = Mock()
        test = Mock()
        # can't create FunctionTestCase... causes str error on import
        # FunctionTestCase(lambda:0, lambda:0, lambda:0)
        test_case = test.unittest_equiv.return_value = Mock()

        before_all, after_all = Mock(), Mock()

        subject = ExampleGroup(before_all, after_all, examples=[test])
        subject = subject.unittest_equiv(Context())

        self.assertEqual(subject, instance)
        self.assertEqual(egte.call_args[0][0], [test_case])


class DescribeExampleGroupEquality(TestCase):
    def create_example(self):
        instance = MagicMock(spec=Example)
        instance.testfn = lambda: 0
        return instance

    def test_it_is_not_equal_to_non_examples(self):
        subject = ExampleGroup(Mock(), Mock(), (), examples=(Mock(),))

        # assertNotEqual doesn't cause this error
        self.assertFalse(subject == Example('foobar'))

    def test_it_is_equal_to_equivalent_group_values(self):
        instance = self.create_example()

        before_all, after_all, parents = Mock(), Mock(), [Mock()]
        examples = [instance]

        subject1 = ExampleGroup(before_all, after_all, parents, examples)
        subject2 = ExampleGroup(before_all, after_all, parents, examples)

        self.assertEqual(subject1, subject2)

    def test_it_is_not_equal_to_different_examples(self):
        instance1 = self.create_example()
        instance2 = self.create_example()

        before_all, after_all, parents = Mock(), Mock(), [Mock()]
        examples1 = [instance1]
        examples2 = [instance2]

        subject1 = ExampleGroup(before_all, after_all, parents, examples1)
        subject2 = ExampleGroup(before_all, after_all, parents, examples2)

        self.assertNotEqual(subject1, subject2)

    def test_it_is_not_equal_to_different_parents(self):
        instance = self.create_example()

        before_all, after_all, examples = Mock(), Mock(), [instance]
        parents1, parents2 = [Mock()], [Mock()]

        subject1 = ExampleGroup(before_all, after_all, parents1, examples)
        subject2 = ExampleGroup(before_all, after_all, parents2, examples)

        self.assertNotEqual(subject1, subject2)

    def test_it_is_not_equal_to_different_after_functions(self):
        instance = self.create_example()

        before_all, parents, examples = Mock(), [Mock()], [instance]
        after_all1, after_all2 = [Mock()], [Mock()]

        subject1 = ExampleGroup(before_all, after_all1, parents, examples)
        subject2 = ExampleGroup(before_all, after_all2, parents, examples)

        self.assertNotEqual(subject1, subject2)

    def test_it_is_not_equal_to_different_before_functions(self):
        instance = self.create_example()

        after_all, parents, examples = Mock(), [Mock()], [instance]
        before_all1, before_all2 = Mock(), Mock()

        subject1 = ExampleGroup(before_all1, after_all, parents, examples)
        subject2 = ExampleGroup(before_all2, after_all, parents, examples)

        self.assertNotEqual(subject1, subject2)


class DescribeExample(TestCase):
    @patch('describe.spec.containers.FunctionTestCase')
    def test_it_can_produce_testcase(self, ftc):
        instance = ftc.return_value = Mock()
        testfn, before, after = Mock(), [Mock()], [Mock()]

        subject = Example(testfn, before, after)

        self.assertEqual(subject.unittest_equiv(Mock()), instance)
        self.assertTrue(ftc.called)

    def test_it_filters_out_non_callables(self):
        fn = Mock()
        testfn, before, after = Mock(), [None, fn, 'foobar'], [fn, None, 1, 2, 3]
        context = Mock()

        subject = Example(testfn, before, after)
        subject.before(context)
        self.assertEqual(fn.call_count, 1)

        subject.after(context)
        self.assertEqual(fn.call_count, 2)

        self.assertEqual(fn.call_args_list, [
            ((), {}),
            ((), {}),
        ])


    def test_it_should_have_func_code_equality(self):
        a, b = lambda:0, lambda:0
        c, d, e, f = lambda: 1, lambda: 2, lambda: 1, lambda: 2

        def g(a, b): return a + b
        def h(a, b): return a + b
        self.assertEqual(Example(a, [c], [d], [g]), Example(b, [e], [f], [h]))

