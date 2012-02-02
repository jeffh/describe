import os
import sys

from describe.spec.utils import locals_from_function
from describe.spec.containers import SpecFile, Context, Example, ExampleGroup


class SpecFinder(object):
    "Finds functions in a module that should be executed as a spec."
    def __init__(self, get_vars=locals_from_function, dirfn=dir):
        self.get_vars = locals_from_function
        self._dir = dirfn # to allow replacement in tests

    def is_spec(self, name, obj):
        return name.startswith('describe_') and callable(obj)

    def is_context(self, name, obj):
        prefixes = ['context_', 'describe_']
        return any(name.startswith(s) for s in prefixes) and callable(obj)

    def is_example(self, name, obj):
        return name.startswith('it_') and callable(obj)

    def extract_examples(self, fn, parents=(), parent_before_each=None, parent_after_each=None):
        local_vars = self.get_vars(fn)
        # prevent infinite recursion....
        if fn.__name__ in local_vars and local_vars[fn.__name__] == fn:
            del local_vars[fn.__name__]

        before_each = local_vars.get('before_each')
        after_each = local_vars.get('after_each')
        before_all = local_vars.get('before_all')
        after_all = local_vars.get('after_all')

        before = list(filter(bool, [before_each, parent_before_each]))
        after = list(filter(bool, [after_each, parent_after_each]))

        parents = parents + (fn,)

        group = ExampleGroup(before_all, after_all, parents)
        for name, obj in local_vars.items():
            if self.is_example(name, obj):
                group.append(Example(obj, before, after, parents))
            if self.is_context(name, obj):
                group.append(self.extract_examples(
                    obj, parents, before_each, after_each))
        return group

    def find(self, module):
        specs = []
        for name in self._dir(module):
            obj = getattr(module, name)
            if self.is_spec(name, obj):
                specs.extend(self.extract_examples(obj))
        return ExampleGroup(examples=specs)


class SpecFileFinder(object):
    "Searches the file system for python files that might contain specs."
    def __init__(self, import_fn=__import__, dir_fn=dir):
        self._import = import_fn
        self._dir = dir_fn

    def find_in_module(self, module):
        specs = []
        for name in self._dir(module):
            obj = getattr(module, name)
            if self.is_spec(obj, name):
                specs.append(obj)
        return specs

    def is_spec(self, obj, name):
        return name.startswith('Describe') or name.startswith('describe_')

    def is_py_file(self, filename):
        return filename.lower().endswith('_spec.py')

    def convert_to_module(self, rel_filepath):
        fp = rel_filepath.replace('\\', '/').replace('/', '.')
        return fp[:-len('.py')]

    def get_module(self, module_path):
        mod = self._import(module_path)
        if '.' in module_path:
            mod = getattr(mod, module_path.rsplit('.', 1)[-1])
        return mod

    def find(self, directory):
        directory = os.path.abspath(directory)
        old_paths = list(sys.path)
        sys.path.insert(0, directory)
        specs = []
        for root, dirs, files in os.walk(directory):
            for filename in files:
                full_path = os.path.join(root, filename)
                if not self.is_py_file(full_path):
                    continue
                module_path = self.convert_to_module(os.path.relpath(full_path, directory))
                #specs = self.get_module(self.get_specs(module_path))
                specs.append(SpecFile(full_path, module_path, self.get_module(module_path)))


        sys.path = old_paths
        return specs

