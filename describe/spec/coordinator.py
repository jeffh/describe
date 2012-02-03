import os
import sys

from describe.spec.finders import SpecFileFinder, SpecFinder
from describe.spec.runners import ExampleRunner
from describe.spec.formatters import StandardResultsFormatter, VerboseResultsFormatter


class SpecCoordinator(object):
    def __init__(self, file_finder=None, spec_finder=None, formatter=None):
        self.file_finder = file_finder or SpecFileFinder()
        self.spec_finder = spec_finder or SpecFinder()
        #self.formatter = formatter or StandardResultsFormatter()
        self.formatter = formatter or VerboseResultsFormatter()

    def find_specs(self, directory):
        specs = []
        spec_files = self.file_finder.find(directory)
        for spec_file in spec_files:
            specs.extend(self.spec_finder.find(spec_file.module))
        return specs

    def execute(self, example_groups):
        for group in example_groups:
            runner = ExampleRunner(group, self.formatter)
            runner.run()

    def run(self, directories=None):
        if directories is None:
            directories = [os.getcwd()]

        for directory in directories:
            self.execute(self.find_specs(directory))

        self.formatter.finalize()

