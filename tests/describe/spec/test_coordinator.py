from unittest import TestCase
from mock import Mock, patch

from describe.spec.coordinator import SpecCoordinator
from describe.spec.containers import ExampleGroup, Example
from describe.spec.finders import SpecFile


class DescribeSpecCoordinator(TestCase):
    def test_finds_specs(self):
        file_finder, spec_finder, formatter  = Mock(), Mock(), Mock()
        spec_files = file_finder.find.return_value = [Mock(), Mock()]
        spec_files[0].modulepath = 'foo.bar_spec'
        spec_files[1].modulepath = 'foo.baz_spec'
        spec_files[0].module = Mock()
        spec_files[1].module = Mock()

        specs = result = [[Mock()], [Mock(), Mock()]]
        expected = specs[0] + specs[1]
        spec_finder.find.side_effect = lambda *args: result.pop(0)

        subject = SpecCoordinator(file_finder, spec_finder, formatter)

        self.assertEqual(subject.find_specs('/foobar/'), expected)

        self.assertEqual(spec_finder.find.call_args_list, [
            ((spec_files[0].module,), {}),
            ((spec_files[1].module,), {}),
        ])

    @patch('describe.spec.coordinator.ExampleRunner')
    def test_executes_spec(self, runner):
        file_finder, spec_finder, formatter = (
            Mock(), Mock(), Mock()
        )
        example_group = ExampleGroup('group', examples=[
            Example('foobar'),
        ])
        instance = runner.return_value = Mock()
        instance.run = Mock(return_value=[1, 2, 3])

        subject = SpecCoordinator(file_finder, spec_finder, formatter)

        subject.execute([example_group])
        instance.run.assert_called_once_with()

    @patch('os.getcwd')
    def test_run_getcwd_as_default(self, getcwd):
        subject = SpecCoordinator(Mock(), Mock(), Mock())
        subject.find_specs = Mock()
        subject.execute = Mock(return_value=[1, 2, 3])

        getcwd.return_value = '/foobar/'

        successes, failures, skipped = subject.run()
        self.assertEqual(successes, 1)
        self.assertEqual(failures, 2)
        self.assertEqual(skipped, 3)

        getcwd.assert_called_once_with()

    def test_run_uses_find_and_then_execute(self):
        subject = SpecCoordinator(Mock(), Mock(), Mock())

        results = [Mock(), Mock()]
        subject.find_specs = Mock(return_value=results)
        subject.execute = Mock(return_value=[1, 2, 3])

        subject.run(('/foo/', '/bar/'))

        self.assertEqual(subject.find_specs.call_args_list, [
            (('/foo/',), {}),
            (('/bar/',), {}),
        ])
        self.assertEqual(subject.execute.call_args_list, [
            ((results,), {}),
            ((results,), {}),
        ])

