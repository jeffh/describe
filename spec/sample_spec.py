import os
import sys
import time

from describe import expect, patch

class DescribeMathOperations:
    def it_should_know_addition(self):
        expect(1 + 1) == 2

    def it_should_know_subtraction(self):
        expect(1 - 1) == 0

    class ContextOrderOfOperations:
        def it_should_be_multiplication_before_addition(self):
            expect(2 * 2 - 1) == 3
            expect(2 + 2) == 6

        #def it_fails():
        #    expect(Foo)

        @patch('time.time')
        def it_failed(mod, c):
            # TODO: this doesn't get run
            mod.expects().and_returns(4)
            expect(time.time()) == 4

    class DescribeContext:
        def before_each(self):
            self.value = 2

        def it_should_have_context(self):
            expect(self.value) == 2

