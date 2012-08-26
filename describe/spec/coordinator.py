import os
import sys

from describe.spec.finders import SpecFileFinder, StandardSpecFinder
from describe.spec.runners import ExampleRunner
from describe.spec.formatters import StandardResultsFormatter


class SpecCoordinator(object):
    """Performs the finding and execution of specs."""
    def __init__(self, file_finder=None, spec_finder=None, formatter=None):
        self.file_finder = file_finder or SpecFileFinder()
        self.spec_finder = spec_finder or StandardSpecFinder()
        self.formatter = formatter or StandardResultsFormatter()

    def find_specs(self, directory):
        """Finds all specs in a given directory. Returns a list of
        Example and ExampleGroup instances.
        """
        specs = []
        spec_files = self.file_finder.find(directory)
        for spec_file in spec_files:
            specs.extend(self.spec_finder.find(spec_file.module))
        return specs

    def execute(self, example_groups):
        """Runs the specs. Returns a tuple indicating the
        number of (succeses, failures, skipped)>
        """
        total_successes, total_errors, total_skipped = 0, 0, 0
        for group in example_groups:
            runner = ExampleRunner(group, self.formatter)
            successes, errors, skips = runner.run()
            total_successes += successes
            total_errors += errors
            total_skipped += skips
        return total_successes, total_errors, total_skipped

    def run(self, directories=None):
        """Finds and runs the specs. Returns a tuple indicating the
        number of (succeses, failures, skipped)>
        """
        if directories is None:
            directories = [os.getcwd()]

        total_successes, total_errors, total_skipped = 0, 0, 0
        for directory in directories:
            successes, errors, skips = self.execute(self.find_specs(directory))
            total_successes += successes
            total_errors += errors
            total_skipped += skips


        self.formatter.finalize()
        return total_successes, total_errors, total_skipped

