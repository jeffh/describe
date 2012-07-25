from unittest import TestCase
from itertools import izip_longest

from describe import expect, matcher


class TestBasicExpectations(TestCase):
    def test_expect_raises_assertion_error_when_no_equal_to(self):
        with self.assertRaises(AssertionError):
            expect(1) == 2

    def test_expect_to_assert_equals(self):
        expect(1) == 1

    def test_expect_to_assert_less_than(self):
        expect(1) < 2

    def test_expect_to_assert_less_than_or_equal(self):
        expect(1) <= 1
        expect(1) <= 2

    def test_expect_to_assert_greater_than(self):
        expect(2) > 1

    def test_expect_to_assert_greater_than_or_equal(self):
        expect(2) >= 2
        expect(2) >= 1

    def test_expect_to_assert_not_equal(self):
        expect(1) != 2

    def test_expect_truthiness(self):
        expect(1).to.be_truthy()

    def test_expect_falsiness(self):
        expect([]).to.be_falsy()

    def test_expect_none(self):
        expect(None).to.be_none()

    def test_expect_inverse(self):
        expect(1).to_not.be_none()

    def test_expect_typeerror_when_assigning_to(self):
        with self.assertRaises(SyntaxError):
            expect(1).to = 1

    def test_expect_typeerror_when_assigning_to_not(self):
        with self.assertRaises(SyntaxError):
            expect(1).to_not = 1


class TestMethodMatchersOnExpectation(TestCase):
    def test_expect_instance_of(self):
        expect(1).to.be_instance_of(int)

    def test_expect_subclass_of(self):
        from collections import defaultdict
        expect(defaultdict).to.be_subclass_of(dict)

    def test_expect_contain(self):
        expect([1, 2, 3]).to.contain(2)
        expect([1, 2, 3]).to.include(1)

    def test_expect_object_instance_equality(self):
        o = object()
        expect(o).to.be_equal(o)
        expect([1, 2]).to_not.be_equal([1, 2])

    def test_expect_float_equality(self):
        expect(1.0 + 1.0 - 1.0).to.be_close_to(1.0)

    def test_expect_float_equality_with_acceptability(self):
        expect(1.0 - 1.0).to.be_close_to(5.0, 10)

    def test_expect_regular_expression_match(self):
        expect('abcdefff').to.match('f+')

    def test_expect_have_subset(self):
        expect(dict(a=1, b=2, c=3)).to.have_subset(dict(a=1, b=2))

    def test_expect_to_have_attr(self):
        print expect(dict).to
        expect(dict()).to.have_attr('keys')

    def test_expect_to_be_callable(self):
        expect(dict().keys).to.be_callable()


class TestInvocationExpectation(TestCase):
    def test_expect_invocation(self):
        expect(lambda a, b: a + b).with_args(1, 2) == 3

    def test_expect_invocation_raises_exception_class(self):
        def runner():
            raise IndexError()
        expect(runner).with_args().to.raise_error(IndexError)

    def test_expect_type_error_when_forgetting_invocation_for_raises_exception(self):
        def runner():
            raise IndexError()
        with self.assertRaises(AssertionError):
            expect(runner).to.raise_error(IndexError)

    def test_expect_with_block_to_raise_error(self):
        with expect.to_raise_error(IndexError):
            raise IndexError()

    def test_expect_as_decoration_to_catch_error(self):
        @expect
        def keyerror():
            raise KeyError()
        keyerror().to.raise_error(KeyError)

    def test_expect_with_block_to_raise_assertion_error_if_block_does_not_raise_error(self):
        with self.assertRaises(AssertionError):
            with expect.to_raise_error(IndexError):
                pass


@matcher(expects_to='be equal as iterators to %(expected)r')
def be_equal_iterable(actual, expected):
    INVALID = object()
    for act, exp  in izip_longest(iter(actual.evaluate()), iter(expected), fillvalue=INVALID):
        if act != exp or INVALID in (act, exp):
            return False
    return True


class TestCustomMatcherExpectations(TestCase):
    def setUp(self):
        expect.add_matcher(be_equal_iterable)

    def tearDown(self):
        expect.remove_matcher(be_equal_iterable)

    def test_custom_matcher(self):
        expect([1, 2, 3]).to.be_equal_iterable((1, 2, 3))

    def test_custom_matcher_fails(self):
        try:
            expect([1, 2, 3]).to.be_equal_iterable((1, 2, 3, 4))
        except AssertionError as ae:
            assert ae.message == 'expected [1, 2, 3] to be equal as iterators to (1, 2, 3, 4)'

    def test_inverse_of_custom_matcher(self):
        expect([1, 2, 3]).to_not.be_equal_iterable((1, 2, 3, 4))


class TestCustomExternalMatcherExpectations(TestCase):
    def test_custom_matcher_as_function_invocation(self):
        expect([1, 2, 3]).to(be_equal_iterable((1, 2, 3)))

    def test_inverse_of_custom_matcher_as_function_invocation(self):
        expect([1, 2, 3]).to_not(be_equal_iterable((1, 2, 3, 4)))

    def test_custom_matcher_fails(self):
        try:
            expect([1, 2, 3]).to(be_equal_iterable((1, 2, 3, 4)))
        except AssertionError as ae:
            assert ae.message == 'expected [1, 2, 3] to be equal as iterators to (1, 2, 3, 4)'
