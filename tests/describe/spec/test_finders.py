import sys
from unittest import TestCase, TestSuite
from cStringIO import StringIO
from itertools import izip_longest

from mock import Mock, MagicMock, patch

from describe.spec.finders import SpecFileFinder, SpecFinder
from describe.spec.containers import ExampleGroup, Example


class ModuleStub(object):
    def __init__(self, *objects, **attributes):
        self.__dict__ = attributes
        for obj in objects:
            self.__dict__[obj.__name__] = obj

    def __getattr__(self, name):
        return self.__dict__[name]

    def __setattr__(self, name, value):
        if hasattr(self, name):
            self.name = value
        else:
            self.__dict__[name] = value


class DescribeSpecFinder(TestCase):
    def example_key(self, obj):
        if isinstance(obj, ExampleGroup):
            return ','.join(sorted(map(self.example_key, obj.examples)))
        return obj.testfn.__name__

    def assertExampleGroupEqual(self, eg1, eg2):
        #self.assertEqual(eg1, eg2)
        exs1 = sorted(eg1, key=self.example_key)
        exs2 = sorted(eg1, key=self.example_key)
        self.assertEqual(len(exs1), len(exs2))
        NULL = object()
        for ex1, ex2 in izip_longest(exs1, exs2, fillvalue=NULL):
            self.assertEqual(ex1, ex2)

class DescribeSpecFinderIdentification(TestCase):
    def setUp(self):
        self.subject = SpecFinder()

    def test_it_can_identify_spec(self):
        self.assertTrue(self.subject.is_spec('describe_cake', Mock()))
        self.assertTrue(self.subject.is_spec('describe_oranges', Mock()))

        self.assertFalse(self.subject.is_spec('Describe_oranges', Mock()))
        self.assertFalse(self.subject.is_spec('DescribeOranges', Mock()))
        self.assertFalse(self.subject.is_spec('Pizza', Mock()))
        self.assertFalse(self.subject.is_spec('Cake', Mock()))
        self.assertFalse(self.subject.is_spec('context_foo', Mock()))

    def test_it_can_identify_context(self):
        self.assertTrue(self.subject.is_context('describe_cake', Mock()))
        self.assertTrue(self.subject.is_context('describe_oranges', Mock()))
        self.assertTrue(self.subject.is_context('context_color', Mock()))

        self.assertFalse(self.subject.is_context('Describe_oranges', Mock()))
        self.assertFalse(self.subject.is_context('DescribeOranges', Mock()))
        self.assertFalse(self.subject.is_context('Pizza', Mock()))
        self.assertFalse(self.subject.is_context('Cake', Mock()))
        self.assertFalse(self.subject.is_context('Context_foo', Mock()))

    def test_it_can_identify_example(self):
        self.assertTrue(self.subject.is_example('it_can_do_stuff', Mock()))
        self.assertTrue(self.subject.is_example('it_makes_up', Mock()))

        self.assertFalse(self.subject.is_example('itCanFly', Mock()))
        self.assertFalse(self.subject.is_example('It_can_fly', Mock()))
        self.assertFalse(self.subject.is_example('itcanfly', Mock()))


class DescribeSpecFinderNested(TestCase):
    def test_it_finds_specs_from_modules(self):
        def describe_cake():
            def before_each(): pass
            def it_should_detect_me(): pass
            def tom_foolery(): pass
            # return to make it easier to test
            return it_should_detect_me, [before_each], [], (describe_cake,)

        def describe_food():
            def context_nested():
                def it_should_allow_contexts(): pass
                def foobar(): pass
                return it_should_allow_contexts
            # return to make it easier to test
            return context_nested(), [], [], (describe_food, context_nested)

        def describe_orange():
            def describe_color():
                def it_should_be_orange(): pass
                return it_should_be_orange
            # return to make it easier to test
            return describe_color(), [], [], (describe_orange, describe_color)

        m = ModuleStub(
            describe_cake, describe_food, describe_orange,
            __name__='TestModule', is_cake_a_lie=True, __version__="9001"
        )

        _dir = Mock(return_value=m.__dict__.keys())
        subject = SpecFinder(_dir)

        _, _, _, parents1 = describe_food()
        _, _, _, parents2 = describe_food()
        expected = ExampleGroup(examples=[
            Example(*describe_cake()),
            ExampleGroup(
                parents=parents1,
                examples=[
                    Example(*describe_food()),
                ]
            ),
            ExampleGroup(
                parents=parents2,
                examples=[
                    Example(*describe_orange()),
                ]
            ),
        ])
        self.maxDiff = None
        # keep it sorted to have an order
        actual = subject.find(m)
        self.assertEqual(actual, expected)


class DescribeSpecFileFinderFeatures(TestCase):
    def setUp(self):
        self._import, self._dir = Mock(), Mock()
        self.subject = SpecFileFinder(self._import, self._dir)

    def test_it_return_true_for_files_ending_in_spec_py(self):
        self.assertTrue(self.subject.is_py_file('foo_spec.py'))

    def test_it_return_false_otherwise(self):
        self.assertFalse(self.subject.is_py_file('foo_spec'))

    def test_it_returns_module_path_from_filepath(self):
        self.assertEqual(self.subject.convert_to_module('foo/bar/lol_spec.py'), 'foo.bar.lol_spec')

    def test_it_returns_module_path_from_filepath(self):
        self.assertEqual(self.subject.convert_to_module('foo/bar/lol_spec.py'), 'foo.bar.lol_spec')

    def test_it_returns_true_for_is_spec_starting_with_describe(self):
        self.assertTrue(self.subject.is_spec(Mock(), 'DescribeFood'))
        self.assertTrue(self.subject.is_spec(Mock(), 'describe_food'))

    def test_it_finds_objects_starting_with_describe(self):
        m = Mock()
        self._dir.return_value = ['__name__', '_private', 'myFunc', 'MyClass', 'DescribeFood', 'describe_cake']
        m.__name__ = "mock"
        m._private = "mock"
        m._myFunc = lambda: 0
        m.MyClass = object
        dfood = m.DescribeFood = Mock()
        dcake = m.describe_cake = Mock()

        self.assertEqual(self.subject.find_in_module(m), [dfood, dcake])

