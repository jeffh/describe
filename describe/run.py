"""Aggregates all global spec running information
"""

class _Collector(object):
    def __init__(self, name):
        self.name = name
        self.fns = []

    def __call__(self, fn):
        self.fns.append(fn)

    def execute(self, context):
        for fn in self.fns:
            fn(context)

    def clear(self):
        self.fns = []

for name in 'before_each before_all after_each after_all'.split(' '):
    globals()[name] = _Collector(name)
