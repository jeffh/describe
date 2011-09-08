import itertools
import operator

try:
    set
except ValueError:
    from sets import Set as set

def ellipses(string, max_length=50):
    if len(string) > max_length:
        string = string[:max_length-7] + ' ... ' + string[-2:]
    return string

def is_iter(obj):
    try:
        for e in obj:
            return True
    except TypeError:
        return False

def diff_dict(dict1, dict2, op=operator.ne):
    MSSING = object()
    for key in set(dict1).union(dict2):
        h = {'key': key, 'x': dict1.get(key, None), 'y': dict2.get(key, None)}
        x, y = h['x'], h['y']
        if key not in dict1:
            del h['x']
        if key not in dict2:
            del h['y']
        if op(x, y):
            return h
    return None

def diff_dict_str(h):
    if not h:
        return ""
    if 'x' in h and 'y' in h:
        return "For key %(key)r, %(x)r should == %(y)r." % h
    elif 'x' in h:
        return "For key %(key)r, %(x)r should == <Dict has no value>." % h
    elif 'y' in h:
        return "For key %(key)r, <Dict has no value> should == %(y)r." % h

def diff_iterables(iter1, iter2, op=operator.ne):
    MISSING = object()
    for i,(x,y) in enumerate(itertools.izip_longest(iter1, iter2, fillvalue=MISSING)):
        h = {'i': i, 'x': x, 'y': y}
        if x == MISSING:
            del h['x']
        if y == MISSING:
            del h['y']
        if op(x, y):
            return h
    return None

def diff_iterable_str(h):
    if not h:
        return ""
    if 'x' in h and 'y' in h:
        return "At element %(i)d, %(x)r should == %(y)r." % h
    elif 'x' in h:
        return "At element %(i)d, %(x)r should == <Missing Element>." % h
    elif 'y' in h:
        return "At element %(i)d, <Missing Element> should == %(y)r." % h
