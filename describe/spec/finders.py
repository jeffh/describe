import os
import sys
import inspect
from cStringIO import StringIO

from describe.utils import Replace
from describe.spec.utils import locals_from_function
from describe.spec.containers import SpecFile, Context, Example, ExampleGroup


class StandardSpecFinder(object):
    """Finds functions in modules and classes that should be executed as a spec.

    Behaves more like traditional python testers - nose, py.test, etc.

    """
    def is_spec(self, name, obj):
        return (name.startswith('describe_') or name.startswith('Describe')) and inspect.isclass(obj)

    def is_context(self, name, obj):
        return self.is_spec(name, obj) or (
            (
             name.startswith('context_') or name.startswith('Context') or
             name.startswith('when_') or name.startswith('When')
            ) and inspect.isclass(obj)
        )

    def is_example(self, name, obj, parent_before_each=None, parent_after_each=None):
        return name.lower().startswith('it_') and callable(obj)

    def _is_valid(self, name, obj):
        return self.is_spec(name, obj) or self.is_context(name, obj) or self.is_example(name, obj)

    def __extract_method(self, obj, name):
        method = getattr(obj, name, None)
        if callable(method):
            return (method,)
        return ()

    def __extract_examples(self, name, obj, parents=(), parent_before_each=(), parent_after_each=()):
        if self.is_spec(name, obj) or self.is_context(name, obj):
            instance = obj()
            before_each = parent_before_each + self.__extract_method(instance, 'before_each')
            after_each = parent_after_each + self.__extract_method(instance, 'after_each')
            newparents = parents + (instance,)
            examples = []
            for n in dir(instance):
                subobj = getattr(instance, n)
                if self._is_valid(n, subobj):
                    example = self.__extract_examples(n, subobj, newparents, before_each, after_each)
                    if example:
                        examples.append(example)
            return ExampleGroup(
                getattr(obj, '__name__', None),
                before=self.__extract_method(instance, 'before_all'),
                after=self.__extract_method(instance, 'after_all'),
                parents=parents,
                examples=examples
            )
        elif self.is_example(name, obj):
            before_each = parent_before_each + self.__extract_method(obj, 'before_each')
            after_each = parent_after_each + self.__extract_method(obj, 'after_each')
            return Example(obj, parents=parents, before=before_each, after=after_each)
        else:
            return None

    def find(self, module):
        specs = []
        for name in dir(module):
            obj = getattr(module, name)
            if self._is_valid(name, obj):
                specs.append(self.__extract_examples(name, obj))
        return ExampleGroup('Specs', examples=specs)

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

