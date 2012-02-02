import types
import traceback
import inspect
import time
from functools import wraps

import byteplay

def fn_returns_locals(f):
    """Modify the function to do:
    try:
        # code
    finally:
        return locals()

    This works for us since we don't have to care about what we need to do.
    Here's from python interpreter::

        >>> def example():
        ...      try:
        ...              print 'hello'
        ...      finally:
        ...              return dict(locals())
        ...
        >>> code = byteplay.Code.from_code(example.func_code)
        >>> pprint(code.code)
        [(SetLineno, 2),
        (SETUP_FINALLY, <byteplay.Label object at 0x100446110>),
        (SetLineno, 3),
        (LOAD_CONST, 'hello'),
        (PRINT_ITEM, None),
        (PRINT_NEWLINE, None),
        (POP_BLOCK, None),
        (LOAD_CONST, None),
        (<byteplay.Label object at 0x100446110>, None),
        (SetLineno, 5),
        (LOAD_GLOBAL, 'dict'),
        (LOAD_GLOBAL, 'locals'),
        (CALL_FUNCTION, 0),
        (CALL_FUNCTION, 1),
        (RETURN_VALUE, None),
        (END_FINALLY, None)]

    """

    fcode = f.func_code
    code = byteplay.Code.from_code(fcode)
    label = byteplay.Label()
    code.code = (
        [
            (byteplay.SETUP_FINALLY, label)
        ]
        + code.code +
        [
            (label, None),
            (byteplay.LOAD_GLOBAL, 'dict'),
            (byteplay.LOAD_GLOBAL, 'locals'),
            (byteplay.CALL_FUNCTION, 0),
            (byteplay.CALL_FUNCTION, 1),
            (byteplay.RETURN_VALUE, None),
            (byteplay.END_FINALLY, None),
        ])
    # build code object again
    f.func_code = code.to_code()
    return f


def locals_from_function(fn):
    localfn = fn_returns_locals(fn)
    context = localfn()
    return {name: value for name, value in context.items() if callable(value)}


def get_true_function(obj):
    "Returns the actual function and a boolean indicated if this is a method or not."
    if not callable(obj):
        raise TypeError("%r is not callable." % (obj,))
    ismethod = inspect.ismethod(obj)
    if inspect.isfunction(obj) or ismethod:
        return obj, ismethod
    if hasattr(obj, 'im_func'):
        return obj.im_func, True
    if inspect.isclass(obj):
        return obj.__init__, True
    if isinstance(obj, object):
        if hasattr(obj, 'func'):
            return get_true_function(obj.func)
        return obj.__call__, True
    raise TypeError("Unknown type of object: %r" % obj)


def func_equal(func1, func2):
    try:
        fn1, _ = get_true_function(func1)
        fn2, _ = get_true_function(func2)
    except TypeError:
        return False
    try:
        # check existance
        return fn1 and fn2 and (
            # equal by location
            (
                # equal location
                getattr(fn1, '__module__', object()) == getattr(fn2, '__module__', object()) and
                getattr(fn1, '__name__', object()) == getattr(fn2, '__name__', object()) and
                # check function equal original functions (for methods)
                getattr(fn1, 'im_func', None) == getattr(fn2, 'im_func', None) and
                # check to make sure we aren't lambdas
                fn1.__name__ != '<lambda>' != fn2.__name__
            ) or
            # equal true functions
            fn1 == fn2 or
            # equal in function code (like two identical lambdas)
            fn1.func_code == fn2.func_code or
            # equal by heuristic - everything but variable names
            (
                fn1.func_code.co_code == fn2.func_code.co_code and
                fn1.func_code.co_consts == fn2.func_code.co_consts and
                fn1.func_code.co_argcount == fn2.func_code.co_argcount and
                len(fn1.func_code.co_varnames) == len(fn2.func_code.co_varnames) and
                fn1.func_code.co_nlocals == fn2.func_code.co_nlocals and
                fn1.func_globals == fn2.func_globals and
                fn1.func_defaults == fn2.func_defaults and
                fn1.func_closure == fn2.func_closure
            )
        )
    except AttributeError:
        return False


def getargspec(obj):
    if not callable(obj):
        raise TypeError("%r is not callable. Cannot read arg spec" % (obj,))
    func, ismethod = get_true_function(obj)
    spec = inspect.getargspec(func)
    # remove self from spec
    if ismethod:
        return inspect.ArgSpec(spec[0][1:], *spec[1:])
    return spec


def accepts_arg(obj):
    try:
        return len(getargspec(obj)[0]) > 0
    except TypeError:
        return False


class CallOnce(object):
    "Wraps a function that will invoke it only once. Subsequent calls are silently ignored."
    COPY_FIELDS = ('__doc__', '__name__', '__module__', 'func_name', 'func_code')
    def __init__(self, func, copy=None):
        self.func = func or None
        self.called = False
        self._copy(copy or self.COPY_FIELDS)

    def _copy(self, names):
        INVALID = object()
        for name in names:
            value = getattr(self.func, name, INVALID)
            if value is not INVALID:
                setattr(self, name, value)

    def __call__(self, *args, **kwargs):
        if not self.called and self:
            self.called = True
            return self.func(*args, **kwargs)

    def __nonzero__(self):
        return callable(self.func)

    def __eq__(self, other):
        return self.func == getattr(other, 'func', other) or func_equal(self.func, other)

    def __repr__(self):
        return "<CallOnce(%r, called=%r)>" % (
            self.func, self.called
        )

def tabulate(string, times=1, indent=4, char=' ', ignore_first=False):
    sb = []
    for i, line in enumerate(string.split('\n')):
        sb.append(char * indent * times + line if (not ignore_first or i != 0) and line.strip() != '' else line)
    return '\n'.join(sb)


class Replace(object):
    def __init__(self, obj, name, value, **kwargs):
        self.obj, self.name, self.value = obj, name, value
        self.noop = kwargs.get('noop', False)

    def set_noop(self, value):
        self.noop = bool(value)
        return self

    def start(self):
        if self.noop: return self
        self._original = getattr(self.obj, self.name)
        setattr(self.obj, self.name, self.value)
        return self

    def stop(self):
        if self.noop: return self
        setattr(self.obj, self.name, self._original)
        return self

    def __enter__(self):
        self.start()
        return self.value

    def __exit__(self, type, info, exception):
        self.stop()

    def __call__(self, fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            with self as obj:
                return fn(obj, *args, **kwargs)
        return decorator


class Benchmark(object):
    def __init__(self):
        self.history = []
        self._last_time = None

    def start(self):
        self._last_time = time.time()
        return self

    def stop(self):
        diff = time.time() - self._last_time
        if self._last_time is None:
            return self.total_time
        self.history.append(diff)
        self._last_time = None
        return self.total_time

    def __enter__(self):
        return self.start()

    def __exit__(self, type, info, exception):
        self.stop()

    @property
    def total_time(self):
        return sum(self.history)


def NOOP():
    pass

