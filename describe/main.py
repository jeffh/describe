#!/usr/bin/env python

import sys
import os
import argparse

from describe.spec.coordinator import SpecCoordinator


class Options(object):
    def __init__(self):
        self.__args = None

    @property
    def args(self):
        assert self.__args is not None, "You must call Options.parse(args) first!"
        return self.__args

    def parse(self, progname=sys.argv[0], args=sys.argv[1:]):
        parser = argparse.ArgumentParser(
            prog=progname,
            description='Runs all specs in a given directory.')
        parser.add_argument('--unittest', '-U', action='store_true',
            help="Allows execution of traditional unit tests based on stdlib's unittest module. (default: %(default)s)")
        parser.add_argument('--verbose', '-V', action='store_true',
            help="Amount of information the runner prints out. (default: %(default)s)")
        parser.add_argument('--trace', '-t', action='store_true',
            help="Prints out full traceback when errors occur (default: %(default)s)")
        parser.add_argument('--color', '-c', action='store_true',
            help="Prints results in color. (default: %(default)s)")
        parser.add_argument('--version', '-v', action='store_true',
            help="Returns version number of %(prog)s.")
        parser.add_argument('--formatter', '-f', default='standard',
            help="Sets the output format. (Defaults to standard)")
        parser.add_argument('--include', '-i', dest='paths', metavar='DIR', action='append',
            default=[], help="Adds the given path to sys.path before running.")

        parser.add_argument('targets', metavar='SPEC_DIRS_OR_FILES', nargs='*',
            help="The directories or files of specs to run. Defaults to current working directory.")

        self.__args = parser.parse_args(args)
        return self

    @property
    def verbosity(self): return int(self.args.verbose)
    @property
    def should_verify_unittests(self): return self.args.unittest
    @property
    def should_show_traceback(self): return self.args.trace
    @property
    def should_use_color(self): return self.args.color
    @property
    def should_show_version(self): return self.args.version

    @property
    def run_targets(self):
        return self.args.targets or [os.getcwd()]

    def append_paths_to(self, paths):
        for path in self.args.paths or ():
            paths.append(path)


class Runner(object):
    def __init__(self, options):
        self.options_parser = options

    def run(self, progn, *args):
        options = self.options_parser.parse(progn, args)
        if options.should_show_version:
            from describe.meta import __version__
            print "Version:", __version__
            return 0
        options.append_paths_to(sys.path)

        # simple for now
        executor = SpecCoordinator()
        num_successes, num_errors, num_skips = executor.run(options.run_targets)

        return num_errors


def main(progn, *args):
    options = Options()
    runner = Runner(options)
    return runner.run(progn, *args)


if __name__ == '__main__':
    sys.exit(main(*sys.argv))
