import os
import sys
import time

from describe import expect, patch, run, Mock, Registry

global_var = False

class DescribeMathOperations:
    def it_should_know_addition(self):
        expect(1 + 1) == 2

    def it_should_know_subtraction(self):
        expect(1 - 1) == 0

    class ContextOrderOfOperations:
        def it_should_be_multiplication_before_addition(self):
            expect(2 * 2 - 1) == 3
            expect(2 + 2) == 4

        #def it_fails():
        #    expect(Foo)

        @patch('time.time')
        def it_failed(mod, c):
            # TODO: this doesn't get run
            mod.expects().and_return(4)
            expect(time.time()) == 4

    class DescribeContext:
        def before_each(self):
            self.value = 2

        def it_should_have_context(self):
            expect(self.value) == 2

    class DescribeGlobalHooks:
        def it_should_have_foo(self):
            expect(self.foo) == 'bar'

        def it_should_have_global_set_to_true(self):
            expect(global_var).to.be_truthy()

    class DescribeMock:
        def it_should_work_with_expectations(self):
            m = Mock()
            m.expects.foobar().called()
            # should error line below is not called
            m.foobar()


@run.before_each
def set(self):
    global global_var
    self.foo = 'bar'
    global_var = True

@run.after_each
def unset(self):
    global global_var
    global_var = False

@run.before_all
def set(self):
    global global_var
    expect(global_var).to.be_falsy()

@run.after_all
def set(self):
    global global_var
    expect(global_var).to.be_falsy()
