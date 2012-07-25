import sys
from unittest import TestCase, TestSuite
from cStringIO import StringIO
from itertools import izip_longest
from collections import defaultdict

from mock import Mock, MagicMock, patch

from describe.spec.finders import SpecFileFinder, StandardSpecFinder
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

class DescribeBaby:
    state = defaultdict(int)
    class ContextInTheBedRoom:
        def before_each(self):
            self.state['bedroom_before_each'] += 1

        def after_each(self):
            self.state['bedroom_after_each'] += 1

        def it_cries(self):
            self.state['bedroom_it_cries'] += 1

    def before_each(self):
        self.state['before_each'] += 1

    def after_each(self):
        self.state['after_each'] += 1

    def it_runs_example(self):
        self.state['example'] += 1

    def it_runs_second_example(self):
        self.state['second_example'] += 1

def reset_describe_baby():
    DescribeBaby.state = defaultdict(int)

class DescribeStandardSpecFinder(TestCase):
    def setUp(self):
        self.subject = StandardSpecFinder()

    class DescribeBaby:
        pass

    def test_it_can_identify_spec(self):
        self.assertTrue(self.subject.is_spec('describe_baby', self.DescribeBaby))
        self.assertTrue(self.subject.is_spec('DescribeBaby', self.DescribeBaby))

        self.assertFalse(self.subject.is_spec('baby_waaah', self.DescribeBaby))
        self.assertFalse(self.subject.is_spec('DescribeInvalid', 534))

    def test_it_can_identify_context(self):
        self.assertTrue(self.subject.is_context('describe_bedroom', self.DescribeBaby))
        self.assertTrue(self.subject.is_context('DescribeBedroom', self.DescribeBaby))
        self.assertTrue(self.subject.is_context('context_bedroom', self.DescribeBaby))
        self.assertTrue(self.subject.is_context('ContextBedroom', self.DescribeBaby))

        self.assertFalse(self.subject.is_spec('DescribeInvalid', 534))
        self.assertFalse(self.subject.is_spec('foo', self.DescribeBaby))
        self.assertFalse(self.subject.is_spec('ContextInvalid', 'lol'))

    def test_it_can_identify_example(self):
        self.assertTrue(self.subject.is_example('it_cries', lambda: 1))
        self.assertFalse(self.subject.is_example('itcries', lambda: 1))
        self.assertFalse(self.subject.is_example('cries', lambda: 1))
        self.assertFalse(self.subject.is_example('it_cries', 2))

class DescribeStandardSpecFinderResults(TestCase):
    def setUp(self):
        self.subject = StandardSpecFinder()
        reset_describe_baby()

    def test_it_can_produce_example_tree(self):
        examples = self.subject.find(ModuleStub(DescribeBaby))
        expected = ExampleGroup('Specs', examples=[
            ExampleGroup(DescribeBaby, examples=[
                ExampleGroup(DescribeBaby.ContextInTheBedRoom, examples=[
                    Example(DescribeBaby.ContextInTheBedRoom.it_cries,
                        parents=[DescribeBaby, DescribeBaby.ContextInTheBedRoom],
                        before=[DescribeBaby.before_each, DescribeBaby.ContextInTheBedRoom.before_each],
                        after=[DescribeBaby.after_each, DescribeBaby.ContextInTheBedRoom.after_each]
                    )],
                    parents=[DescribeBaby()],
                ),
                Example(DescribeBaby.it_runs_example,
                    parents=[DescribeBaby],
                    before=[DescribeBaby.before_each],
                    after=[DescribeBaby.after_each],
                ),
                Example(DescribeBaby.it_runs_second_example,
                    parents=[DescribeBaby],
                    before=[DescribeBaby.before_each],
                    after=[DescribeBaby.after_each],
                )
            ])
        ])
        self.assertEqual(examples, expected)


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

