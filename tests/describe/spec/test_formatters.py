from types import TracebackType
from unittest import TestCase
from cStringIO import StringIO
from mock import Mock, MagicMock, patch

from describe.spec.formatters import StandardResultsFormatter, ErrorFormat, MinimalResultsFormatter, filtered_traceback
from describe.spec.containers import Example, ExampleGroup
from tests.describe.spec.shared_utils import SampleError


class DescribeFilteredTraceback(TestCase):
    @patch('traceback.format_exception')
    def it_should_stop_emitting_when_marker_is_found(self, format_exception):
        error = MagicMock(spec=Exception)

        tb = Mock(spec=TracebackType)
        tb.__contains__.return_value = False
        target = tb.tb_next.tb_next.tb_next
        target.tb_frame.f_globals.__contains__.return_value = True

        format_exception.return_value = 'foo'

        self.assertEqual(filtered_traceback(error, tb), "foo")
        format_exception.assert_called_once_with(Exception, error, target)

    def it_should_return_traceback_if_its_not_a_traceback_type(self):
        tb = 'bar'

        self.assertEqual(filtered_traceback(Mock(), tb), "bar")


def set_examples(r, passed, skipped=0, errors=[]):
    r.num_examples = passed + len(errors)
    r.num_passed = passed
    r.num_failed = len(errors)
    r.num_skipped = skipped
    r.errors = errors

def set_timings(r, real=3, user=2):
    r.total_real_time = real
    r.total_user_time = user


class DescribeErrorFormat(TestCase):
    def test_it_outputs_parents_before_error(self):
        parent1 = Mock()
        parent1.name = 'describe_cake'
        parent2 = Mock()
        parent2.name = 'context_color'
        error = ErrorFormat(
            'It should do stuff', AssertionError('Expected 2 to be 1'), 'Traceback',
            (parent1, parent2)
        )

        output = error.format_with_parent_names("%(name)s:\n%(traceback)s\n")
        self.assertMultiLineEqual(output, """describe_cake
    context_color
        It should do stuff:
            Traceback
""")

    def test_it_outputs_human_readable_string(self):
        error = ErrorFormat(
            'It should do stuff', AssertionError('Expected 2 to be 1'), 'Traceback'
        )

        self.assertMultiLineEqual(str(error), """It should do stuff:
    Traceback
""")

    def test_it_outputs_exception_if_not_assertion_error(self):
        error = ErrorFormat(
            'It should do stuff', TypeError('Expected 2 to be 1'), 'Traceback'
        )

        self.assertMultiLineEqual(str(error), """It should do stuff:
    Traceback
""")

    def test_it_outputs_stdout_if_provided(self):
        error = ErrorFormat(
            'It should do stuff', TypeError('Expected 2 to be 1'), 'Traceback',
            stdout='foobar\n',
        )

        self.assertMultiLineEqual(str(error), """It should do stuff:
    Traceback

        -------------------->> from stdout <<--------------------
        foobar

        -------------------->> end stdout  <<--------------------
""")

    def test_it_outputs_stderr_if_provided(self):
        error = ErrorFormat(
            'It should do stuff', TypeError('Expected 2 to be 1'), None,
            stderr='foobar\n',
        )

        self.assertMultiLineEqual(str(error), """It should do stuff:
    TypeError: Expected 2 to be 1.

        -------------------->> from stderr <<--------------------
        foobar

        -------------------->> end stderr  <<--------------------
""")

    def test_it_outputs_stdout_and_stderr_if_provided(self):
        error = ErrorFormat(
            'It should do stuff', TypeError('Expected 2 to be 1'), None,
            stdout='foobar\n', stderr='lol\n',
        )

        self.assertMultiLineEqual(str(error), """It should do stuff:
    TypeError: Expected 2 to be 1.

        -------------------->> from stdout <<--------------------
        foobar

        -------------------->> end stdout  <<--------------------

        -------------------->> from stderr <<--------------------
        lol

        -------------------->> end stderr  <<--------------------
""")


class DescribeStandardResultsFormatter(TestCase):
    "Outputs like nosetests."
    def setUp(self):
        self.stdout = StringIO()
        self.r = StandardResultsFormatter(stdout=self.stdout, pass_char='.', fail_char='F', skip_char='S')

    def test_it_asserts_groups_are_popped_in_reverse_ordered_they_were_added(self):
        formatter = Mock()

        example1 = ExampleGroup(None, None, None, (1, 2, 3))
        example2 = ExampleGroup(None, None, None, (2, 3, 4))

        subject = StandardResultsFormatter()
        subject.start_example_group(example1)
        subject.start_example_group(example2)
        with self.assertRaises(AssertionError):
            subject.end_example_group(example1)

    def test_it_should_record_successful_example(self):
        real_time, user_time = 2, 1
        error = traceback = None
        example = Example('it_should_work', real_time=2, user_time=1)
        self.r.record_example(example)

        self.assertEqual(self.r.num_examples, 1)
        self.assertEqual(self.r.num_passed, 1)
        self.assertEqual(self.r.total_real_time, 2)
        self.assertEqual(self.r.total_user_time, 1)
        stdout = self.stdout.getvalue()
        self.assertIn('.', stdout)

    def test_it_should_record_failed_example(self):
        real_time, user_time = 3, 1
        error, traceback = TypeError('foobar'), Mock()
        example = Example(
            'It should do stuff',
            real_time=3, user_time=1,
            error=error, traceback=traceback)
        self.r.record_example(example)

        self.assertEqual(self.r.num_examples, 1)
        self.assertEqual(self.r.num_failed, 1)
        self.assertEqual(self.r.total_real_time, 3)
        self.assertEqual(self.r.total_user_time, 1)
        stdout = self.stdout.getvalue()
        self.assertIn('F', stdout)

    def test_it_should_record_example_group(self):
        real_time, user_time = 2, 1
        self.r.start_example_group('describe_cake')
        self.r.end_example_group('describe_cake')

        self.assertEqual(self.r.num_groups, 1)

    def test_finalize_uses_write_errors_and_write_summary(self):
        self.r.write_errors = Mock(return_value='')
        self.r.write_summary = Mock(return_value='')

        self.r.finalize()

        self.r.write_errors.assert_called_once_with()
        self.r.write_summary.assert_called_once_with()


class DescribeStandardResultsFormatterWriteSummary(TestCase):
    def setUp(self):
        self.stdout = StringIO()
        self.r = StandardResultsFormatter(stdout=self.stdout, pass_char='', fail_char='', skip_char='')

    def test_it_should_write_out_stats_with_errors_and_no_skipped(self):
        set_examples(self.r, passed=1, skipped=0, errors=[
            ErrorFormat('it_should_do_stuff', AssertionError('expect 2 to be 1'), 'traceback'),
        ])
        set_timings(self.r, real=3, user=2)
        self.r.write_summary()

        output = """
==================================================
Ran 2 examples in 2.00s (real=3.00s).

FAILED (errors=1)
"""
        self.assertMultiLineEqual(self.stdout.getvalue(), output)

    def test_it_should_write_out_stats_with_errors_with_skipped(self):
        set_examples(self.r, passed=1, skipped=1, errors=[
            ErrorFormat('it_should_do_stuff', AssertionError('expect 2 to be 1'), 'traceback'),
        ])
        set_timings(self.r, real=99.45, user=33.3)
        self.r.write_summary()

        output = """
==================================================
Ran 2 examples in 33.30s (real=99.45s).

FAILED (errors=1,skipped=1)
"""
        self.assertMultiLineEqual(self.stdout.getvalue(), output)

    def test_it_should_write_OK_for_all_passing(self):
        set_examples(self.r, passed=1, skipped=0, errors=[])
        self.r.write_summary()

        output = """
==================================================
Ran 1 example in 0.00s (real=0.00s).

OK
"""
        self.assertMultiLineEqual(self.stdout.getvalue(), output)

    def test_it_should_write_OK_and_skipp_count_for_all_passing_and_skipped(self):
        set_examples(self.r, passed=10, skipped=3, errors=[])
        self.r.write_summary()

        output = """
==================================================
Ran 10 examples in 0.00s (real=0.00s).

OK (skipped=3)
"""
        self.assertMultiLineEqual(self.stdout.getvalue(), output)

class DescribeStandardResultsFormatterWriteErrors(TestCase):
    def setUp(self):
        self.stdout = StringIO()
        self.r = StandardResultsFormatter(stdout=self.stdout, pass_char='', fail_char='', skip_char='')

    def test_it_should_write_nothing_for_no_errors(self):
        set_examples(self.r, passed=1, skipped=2, errors=[])
        self.r.write_errors()

        output = ""
        self.assertMultiLineEqual(self.stdout.getvalue(), output)

    @patch.object(ErrorFormat, 'format')
    def test_it_should_write_out_error(self, errstr):
        set_examples(self.r, passed=1, skipped=1, errors=[
            ErrorFormat('it_should_do_stuff', AssertionError('expect 2 to be 1'), 'traceback'),
        ])
        errstr.return_value = 'error'

        self.r.write_errors()

        output = """
==================================================
error
"""
        self.assertMultiLineEqual(self.stdout.getvalue(), output)
        self.assertEqual(errstr.call_count, 1)

    @patch.object(ErrorFormat, 'format')
    def test_it_should_write_out_errors(self, errstr):
        set_examples(self.r, passed=1, skipped=1, errors=[
            ErrorFormat(None, None, None),
            ErrorFormat(None, None, None),
        ])
        errstr.return_value = 'error'

        self.r.write_errors()

        output = """
==================================================
error

error
"""
        self.assertMultiLineEqual(self.stdout.getvalue(), output)
        self.assertEqual(errstr.call_count, 2)


class DescribeMinimalResultsFormatter(TestCase):
    def setUp(self):
        self.stdout = StringIO()
        self.r = MinimalResultsFormatter(stdout=self.stdout)

    @patch.object(ErrorFormat, 'format')
    def test_it_should_write_out_errors(self, errstr):
        set_examples(self.r, passed=1, skipped=1, errors=[
            ErrorFormat(None, None, None),
            ErrorFormat(None, None, None),
        ])
        errstr.return_value = 'error'

        self.r.write_errors()

        output = """
error

error
"""
        self.assertMultiLineEqual(self.stdout.getvalue(), output)
        self.assertEqual(errstr.call_count, 2)

    def test_it_should_write_OK_and_skip_count_for_all_passing_and_skipped(self):
        set_examples(self.r, passed=10, skipped=3, errors=[])
        self.r.write_summary()

        output = """
Ran 10 examples in 0.00s (real=0.00s).

OK (skipped=3)
"""
        self.assertMultiLineEqual(self.stdout.getvalue(), output)

