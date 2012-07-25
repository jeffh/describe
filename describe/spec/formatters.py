"""spec_formatter.py - Spec result formatter classes

These classes emit appropriate output given the methods acted
upon them by Example and ExampleGroup classes.
"""
import sys
import traceback
import types

from describe.spec.utils import tabulate, filter_traceback


def prettyprint_camelcase(name):
    s = []
    for c in name:
        if c.upper() == c:
            s.append(' ')
        s.append(c.lower())
    return ''.join(s)

def prettyprint_underscore_notation(name):
    return name.replace('_', ' ').replace('  ', ' ').lower()

def prettyprint(name):
    return prettyprint_underscore_notation(prettyprint_camelcase(name)).strip()


class ErrorFormat(object):
    "Represents an error in an example and all it's associated data."
    def __init__(self, name, error, traceback, parents=(), stdout='', stderr=''):
        self.name = name
        self.error, self.traceback, = error, traceback
        self.stdout, self.stderr = stdout, stderr
        self.parents = parents
        #assert isinstance(self.error, Exception) or (
        #    isinstance(self.error, type) and issubclass(self.error, Exception)), \
        #            "Error must be an Exception subclass"

    def __repr__(self):
        return "ErrorFormat(%r, %r, %r, %r, %r)" % (
            self.name, self.error, self.traceback, self.stdout, self.stder
        )

    def _format(self):
        if self.traceback:
            return "%(parents)s%(name)s:\n%(traceback)s\n"
        return "%(parents)s%(name)s:\n%(error)s.\n%(traceback)s\n"

    def _stream(self, stream, name):
        sb = []
        line = '-' * 20
        sb.append('')
        sb.append(line + ('>> from %s <<' % name) + line)
        sb.append(stream)
        sb.append(line + ('>> end %s  <<' % name) + line)
        return tabulate('\n'.join(sb))

    def _stdout(self):
        return self._stream(self.stdout, 'stdout')

    def _stderr(self):
        return self._stream(self.stderr, 'stderr')

    def _traceback(self):
        sb = []
        if self.traceback:
            sb.append(filter_traceback(self.error, self.traceback or None))
        if self.stdout:
            sb.append(self._stdout())
        if self.stderr:
            sb.append(self._stderr())

        return '\n'.join(filter(bool, sb))

    def _error(self):
        if isinstance(self.error, AssertionError):
            return self.error.message
        return self.error.__class__.__name__ + ': ' + str(self.error)

    def _parents(self):
        if not self.parents:
            return ''
        sb = []
        for i, parent in enumerate(self.parents):
            if parent.name:
                sb.append(tabulate(prettyprint(parent.name), times=i))
        return '\n'.join(sb) + '\n'

    def _num_parents(self):
        return sum(1 for parent in self.parents if parent.name)

    def format_with_parent_names(self, formatstr):
        return self._parents() + tabulate(self.format(formatstr), times=self._num_parents())

    def format(self, formatstr):
        return tabulate(formatstr % {
            'parents': self._parents(),
            'name': prettyprint(str(self.name)),
            'error': self._error(),
            'traceback': self._traceback(),
        }, ignore_first=True).rstrip() + '\n'

    def __str__(self):
        return self.format(self._format())


class StandardResultsFormatter(object):
    "The default formatter for outputting spec results to the console."
    def __init__(self, stdout=sys.stdout, pass_char='.', fail_char='F', skip_char='S'):
        self.stdout = stdout
        self.num_examples = self.num_passed = self.num_failed = self.num_skipped = 0
        self.num_groups = 0
        self.total_real_time = self.total_user_time = 0
        self.pass_char, self.fail_char, self.skip_char = pass_char, fail_char, skip_char
        self.errors = []
        self.group_stack = []

    def __repr__(self):
        return "StandardResultsFormatter(stdout=%r, pass_char=%r, fail_char=%r, skip_char=%r)" %(
            self.stdout, self.pass_char, self.fail_char, self.skip_char
        )

    def skip_example(self, example):
        self.num_skipped += 1
        self._write_example_skipped(example)

    def start_example_group(self, example):
        self.num_groups += 1
        self.group_stack.append(example)

    def end_example_group(self, example):
        assert self.group_stack[-1] == example, "Example Group to remove must be the most recent started."
        self.group_stack.pop()

    def skip_example_group(self, example):
        pass

    def record_example(self, example):
        """Records an example's (aka, unittest's) results. If error is specified, records the
        run as a failure.

        Returns True if the example passed and False on failure.
        """
        self.num_examples += 1
        self.total_real_time += example.real_time
        self.total_user_time += example.user_time
        if not example.error:
            self.num_passed += 1
            self._write_example_passed(example)
        else:
            self.num_failed += 1
            self._write_example_failed(example)
            error = ErrorFormat(
                example.name, example.error, example.traceback,
                tuple(self.group_stack), example.stdout, example.stderr
            )
            self.errors.append(error)
        return not example.error

    def finalize(self):
        "Shorthand for calling write_errors() and write_summary()."
        self.write_errors()
        self.write_summary()

    def write_errors(self):
        if self.errors:
            self._write("%(line)s\n%(errors)s\n" % {
                'line': self._errorsline(),
                'errors': self._errors(),
            })

    def write_summary(self):
        self._write("%(line)s\n%(totals)s\n\n%(status)s\n" % {
            'line': self._summaryline(),
            'totals': self._totalsline(),
            'status': self._statusline(),
        })

    ################ Private methods
    def _errors(self):
        return '\n\n'.join(self._error_format(e) for e in self.errors)

    def _error_format(self, error):
        if error.traceback:
            return error.format_with_parent_names("%(name)s:\n%(traceback)s\n")
        else:
            return error.format_with_parent_names("%(name)s:\n%(error)s.\n%(traceback)s\n")

    def _errorsline(self):
        return '\n' + '=' * 50

    def _summaryline(self):
        return '\n' + '=' * 50

    def _totalsline(self):
        return "Ran %d example%s in %.2fs (real=%.2fs)." % (
            self.num_examples,
            's' if self.num_examples != 1 else '',
            self.total_user_time,
            self.total_real_time,
        )

    def _statusline(self):
        statusline = "OK"
        if self.num_failed:
            if self.num_skipped:
                statusline = "FAILED (errors=%d,skipped=%d)" % (self.num_failed, self.num_skipped)
            else:
                statusline = "FAILED (errors=%d)" % self.num_failed
        elif self.num_skipped:
            statusline = "OK (skipped=%d)" % self.num_skipped
        return statusline

    def _write_example_failed(self, example):
        self._write(self.fail_char)

    def _write_example_skipped(self, example):
        self._write(self.skip_char)

    def _write_example_passed(self, example):
        self._write(self.pass_char)

    def _write(self, message):
        if message != '':
            self.stdout.write(message)
            self.stdout.flush()


class MinimalResultsFormatter(StandardResultsFormatter):
    "An alternative formatter that reduces as much of its output as possible."
    def __init__(self, stdout=sys.stdout, pass_char='', fail_char='', skip_char=''):
        super(MinimalResultsFormatter, self).__init__(
            stdout=stdout, pass_char=pass_char, fail_char=fail_char, skip_char=skip_char
        )

    def _errorsline(self):
        return ''

    def _summaryline(self):
        return ''

    def _totalsline(self):
        return "Ran %d example%s in %.2fs (real=%.2fs)." % (
            self.num_examples,
            's' if self.num_examples != 1 else '',
            self.total_user_time,
            self.total_real_time,
        )

    def _statusline(self):
        statusline = "OK"
        if self.num_failed:
            if self.num_skipped:
                statusline = "FAILED (errors=%d,skipped=%d)" % (self.num_failed, self.num_skipped)
            else:
                statusline = "FAILED (errors=%d)" % self.num_failed
        elif self.num_skipped:
            statusline = "OK (skipped=%d)" % self.num_skipped
        return statusline


