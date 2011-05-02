import itertools
import operator

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