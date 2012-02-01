from describe import expect, patch


def describe_math_operations():
    def it_should_know_addition():
        expect(1 + 1) == 2

    def it_should_know_subtraction():
        expect(1 - 1) == 0

    def describe_order_of_operations():
        def it_should_be_multiplication_before_addition():
            expect(2 * 2 - 1) == 3

        #def it_fails():
        #    expect(Foo)

        @patch.all()
        def it_failed(mod):
            import time
            expect(time.time()) == 4
