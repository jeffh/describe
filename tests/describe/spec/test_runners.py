import sys
from unittest import TestCase

from mock import Mock, MagicMock, patch

from describe.spec.containers import ExampleGroup, Example
from describe.spec.runners import ExampleRunner


class DescribeExampleRunner(TestCase):
    @patch('describe.spec.runners.locals_from_function')
    @patch('describe.spec.runners.Benchmark')
    def test_it_executes_all_its_examples(self, Benchmark, lff):
        before, after = Mock(), Mock()
        example = Example(Mock(), [], [])
        Benchmark.return_value = MagicMock()
        lff.return_value = {}

        examplegroup = ExampleGroup(before, after, examples=[example])
        subject = ExampleRunner(examplegroup, Mock())
        self.assertTrue(subject.execute(stdout=sys.stdout))

        self.assertNotEqual(example.stdout, None)
        self.assertNotEqual(example.stderr, None)


class DescribeExampleRunner(TestCase):
    @patch('describe.spec.runners.Benchmark')
    def test_it_records_timings(self, Benchmark):
        results = [MagicMock(), MagicMock()]
        results[0].total_time = results[0].stop.return_value = 1
        results[1].total_time = results[1].stop.return_value = 2
        Benchmark.side_effect = lambda: results.pop(0)

        example = Example(Mock(), [], [])
        subject = ExampleRunner(example, Mock())
        subject.run()

        self.assertEqual(example.real_time, 1)
        self.assertEqual(example.user_time, 2)

    @patch('describe.spec.runners.Benchmark')
    def test_it_records_basic_stats(self, Benchmark):
        testfn, before, after = Mock(), Mock(), Mock()
        Benchmark.return_value = MagicMock()

        example = Example(testfn, [before], [after])
        subject = ExampleRunner(example, Mock())
        self.assertFalse(subject.has_ran)

        self.assertTrue(subject.execute())

        self.assertTrue(subject.has_ran)
        testfn.assert_called_once_with()
        before.assert_called_once_with()
        after.assert_called_once_with()

    @patch('describe.spec.runners.Benchmark')
    def test_it_records_raised_errors(self, Benchmark):
        Benchmark.return_value = MagicMock()

        def testfn():
            raise IOError("muhaha")

        example = Example(testfn, [], [])
        subject = ExampleRunner(example, Mock())
        subject.execute()

        self.assertEqual(example.error.message, "muhaha")
        self.assertTrue(isinstance(example.error, IOError))


    @patch('describe.spec.runners.Benchmark')
    def test_it_records_std_streams(self, Benchmark):
        Benchmark.return_value = MagicMock()

        def testfn():
            print 'hello world'
            print >>sys.stderr, "hello from stderr"

        example = Example(testfn, [], [])
        subject = ExampleRunner(example, Mock())
        subject.execute()

        self.assertEqual(example.stderr.getvalue(), "hello from stderr\n")
        self.assertEqual(example.stdout.getvalue(), "hello world\n")

    def test_it_knows_when_it_can_be_skipped(self):
        example = Example(None, [], [])
        subject = ExampleRunner(example, Mock())
        self.assertTrue(subject.should_skip())

    def test_it_knows_when_it_can_not_be_skipped(self):
        def testfn(c):
            pass

        example = Example(testfn, [], [])
        subject = ExampleRunner(example, Mock())
        self.assertFalse(subject.should_skip())

class DescribeExampleRunnerInteractingWithFormatterAndExample(TestCase):
    @patch('describe.spec.runners.Benchmark')
    def test_it_records_success_run_to_formatter(self, Benchmark):
        instance = Benchmark.return_value = MagicMock()
        instance.total_time = 2

        formatter = Mock()

        def testfn():
            pass

        example = Example(testfn, [], [])
        subject = ExampleRunner(example, formatter)
        subject.execute()

        formatter.record_example.assert_called_once_with(example)

    @patch('describe.spec.runners.Benchmark')
    def test_it_records_failed_run_to_formatter(self, Benchmark):
        instance = Benchmark.return_value = MagicMock()

        formatter = Mock()
        error = TypeError('idk')

        def testfn():
            raise error

        example = Example(testfn, [], [])
        subject = ExampleRunner(example, formatter)
        subject.execute()

        traceback_cmp = MagicMock()
        traceback_cmp.__eq__ = lambda s, o: 'Traceback' in o and 'line' in o

        formatter.record_example.assert_called_once_with(example)

    @patch('describe.spec.runners.Benchmark')
    def test_it_records_skipped_to_formatter(self, Benchmark):
        formatter = Mock()
        def testfn():
            pass

        example = Example(testfn, [], [])
        subject = ExampleRunner(example, formatter)
        subject.should_skip = Mock(return_value=True)
        subject.run()

        formatter.skip_example.assert_called_once_with(example)

class DescribeExampleRunnerInteractingWithFormatterAndExampleGroup(TestCase):
    @patch('describe.spec.runners.Benchmark')
    def test_it_records_success_run_to_formatter(self, Benchmark):
        instance = Benchmark.return_value = MagicMock()
        formatter = Mock()

        example = ExampleGroup((), None, None)
        subject = ExampleRunner(example, formatter)
        subject.execute()

        formatter.start_example_group.assert_called_once_with(example)
        formatter.end_example_group.assert_called_once_with(example)


    @patch('describe.spec.runners.Benchmark')
    def test_it_records_skipped_to_formatter(self, Benchmark):
        formatter = Mock()

        example = ExampleGroup((), None, None)
        subject = ExampleRunner(example, formatter)
        subject.should_skip = Mock(return_value=True)
        subject.run()

        formatter.skip_example_group.assert_called_once_with(example)

