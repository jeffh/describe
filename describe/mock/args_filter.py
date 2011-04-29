import re

__ALL__ = ['ANYTHING', 'ANY_ARG', 'ARGS', 'KWARGS', 'an_instance_of', 'boolean', 'regexp',
    'duck_type', 'includes_pair', 'filters']

class ArgFilter(object):
    def __init__(self, name):
        self.name = name
        self.func = lambda x: True
        self.comment =''
    
    def __repr__(self):
        return "<%s%s>" % (self.name, self.comment)
        
    def __call__(self, func):
        self.func = func
        return self
        
    def __eq__(self, other):
        return self.name == getattr(other, 'name', None) and self.func == getattr(other, 'func', None)
    
    def verify(self, arg):
        return self.func(arg)

class MultiArgFilters(ArgFilter):
    def __init__(self, *filters):
        self.name = 'multiple_filters'
        self.funcs = tuple(filters)
        
    def __eq__(self, other):
        return self.name == other.name and self.funcs == other.funcs

    def verify(self, arg):
        for v in self.funcs:
            if not v(arg):
                return False
        return True
filters = MultiArgFilters

@ArgFilter('MISSING_ARG')
def MISSING_ARG(obj):
    return False
    
ANYTHING = ArgFilter('ANYTHING')
@ArgFilter('ANY_ARG')
def ANY_ARG(obj):
    return type(obj) != ArgFilter or obj.name != 'MISSING_ARG'
    
ARGS = ArgFilter('*args')
KWARGS = ArgFilter('**kwargs')

def an_instance_of(the_type):
    @ArgFilter('instance_of')
    def aio(obj):
        return type(obj) == the_type
    aio.comment = '(%s)' % the_type.__name__
    return aio
    
boolean = an_instance_of(bool)
regexp = an_instance_of(type(re.compile('')))

def includes_pair(key, value):
    @ArgFilter('includes_pair')
    def di(obj):
        return hasattr(obj, 'get') and obj.get(key, False) == value
    di.comment = '{%r: %r}' % (key, value)
    return di

def duck_type(*attributes):
    @ArgFilter('duck_type')
    def dt(obj):
        for key in attributes:
            if not hasattr(obj, key):
                return False
        return True # TODO: stub out
    dt.comment = '(%s)' % ', '.join(attributes)
    return dt