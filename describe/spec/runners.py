import sys
import traceback
from unittest import FunctionTestCase, TestSuite
from itertools import izip_longest
from cStringIO import StringIO

from describe.mock.registry import Registry
from describe.spec.containers  import Context, ExampleGroup, Example
from describe.utils import Replace
from describe.spec.utils import Benchmark, CallOnce, \
        accepts_arg, get_true_function, func_equal, tabulate, NOOP
from describe import run


class ExampleRunner(object):
    def __init__(self, example, formatter):
        self.example, self.formatter = example, formatter
        self.has_ran = False
        self.is_root_runner = False
        self.num_successes = 0
        self.num_failures = 0
        self.num_skipped = 0

    def __repr__(self):
        return "ExampleRunner(%r, %r)" % (self.example, self.formatter)

    def should_skip(self):
        return (not callable(self.example.testfn) and not len(self.example))

    def execute(self, context=None, stdout=None, stderr=None):
        """Does all the work of running an example.

        This includes:
        - building up the context.
        - capturing stdout & stderr
        - execute before functions
        - run example, catching any exceptions
        - execute after functions
        - record the results & timings to formatter and original example object
        """
        total_benchmark = Benchmark()
        self.context = context or Context()
        if self._is_collection():
            self.stdout = sys.stdout
            self.stderr = sys.stderr
        else:
            self.stdout = stdout or StringIO()
            self.stderr = stderr or StringIO()
        self._record_start_example(self.formatter)
        try:
            with total_benchmark, Replace(sys, 'stdout', self.stdout), Replace(sys, 'stderr', self.stderr):
                self._setup()
                self._execute()
                self._teardown()
        except Exception as e:
            self.example.error = e
            self.example.traceback = sys.exc_info()[2] #traceback.format_exc()
        finally:
            self.example.real_time = total_benchmark.total_time
            self._record_end_example(self.formatter)
            self.context = None
            self.example.stdout = self.stdout
            self.example.stderr = self.stderr
        return self.example.error is None

    def run(self, context=None, stdout=None, stderr=None):
        "Like execute, but records a skip if the should_skip method returns True."
        if self.should_skip():
            self._record_skipped_example(self.formatter)
            self.num_skipped += 1
        else:
            self.execute(context, stdout, stderr)
        return self.num_successes, self.num_failures, self.num_skipped

    #################### Internal Methods ####################
    def _setup(self):
        "Resets the state and prepares for running the example."
        self.example.error = None
        self.example.traceback = ''
        # inject function contexts from parent functions
        c = Context(parent=self.context)
        #for parent in reversed(self.example.parents):
        #    c._update_properties(locals_from_function(parent))
        self.context = c
        if self.is_root_runner:
            run.before_all.execute(self.context)
        self.example.before(self.context)

    def _is_collection(self):
        """Returns True if the given example is a collection of examples
        (aka, ExampleGroup), or just one example.

        """
        try:
            iter(self.example)
            return True
        except TypeError:
            return False

    def _execute(self):
        "Executes the example."
        # IDEA: this is some code smell....
        # perhaps break into two classes and have another
        # class as the interface.
        if self._is_collection():
            self._execute_example_group()
        else:
            self._execute_example()

    def _execute_example_group(self):
        "Handles the execution of Example Group"
        for example in self.example:
            runner = self.__class__(example, self.formatter)
            runner.is_root_runner = False
            successes, failures, skipped = runner.run(self.context)
            self.num_successes += successes
            self.num_failures += failures
            self.num_skipped += skipped

    def _execute_example(self):
        "Handles the execution of the Example"
        test_benchmark = Benchmark()
        try:
            with Registry(), test_benchmark:
                if accepts_arg(self.example.testfn):
                    self.example.testfn(self.context)
                else:
                    self.context.inject_into_self(self.example.testfn)
                    self.example.testfn()
                self.num_successes += 1
        except KeyboardInterrupt:
            # bubble interrupt for canceling spec execution
            raise
        except:
            raise
            self.num_failures += 1
        finally:
            self.example.user_time = test_benchmark.total_time

    def _teardown(self):
        "Handles the restoration of any potential global state set."
        self.example.after(self.context)
        if self.is_root_runner:
            run.after_all.execute(self.context)
        #self.context = self.context._parent
        self.has_ran = True

    def _record_start_example(self, formatter):
        if self._is_collection():
            formatter.start_example_group(self.example)

    def _record_end_example(self, formatter):
        if self._is_collection():
            formatter.end_example_group(self.example)
        else:
            formatter.record_example(self.example)

    def _record_skipped_example(self, formatter):
        if self._is_collection():
            formatter.skip_example_group(self.example)
        else:
            formatter.skip_example(self.example)

