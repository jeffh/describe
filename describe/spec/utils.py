import types
import traceback
import inspect
import time
from functools import wraps


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


def func_equal(fn1, fn2):
    try:
        fn1, _ = get_true_function(fn1)
        fn2, _ = get_true_function(fn2)
    except TypeError:
        return False
    try:
        return fn1 and fn2 and (
            fn1 == fn2 or
            fn1.func_code == fn2.func_code or
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
        self.func = func
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


class LocalsExtractor(object):
    "Extracts function following a given context"
    def __init__(self, fn):
        self.fn = fn
        self.__functions = None

    def _get_code(self):
        return dict(inspect.getmembers(self.fn))['func_code']

    def _get_constants(self):
        return [(c.co_name, c) for c in self._get_code().co_consts if isinstance(c, types.CodeType)]

    def _get_function(self, code):
        return types.FunctionType(code, self.fn.func_globals)

    def _get_functions(self):
        obj = {}
        for name, code in self._get_constants():
            obj[name] = self._get_function(code)
        return obj

    @property
    def functions(self):
        if self.__functions is None:
            self.__functions = self._get_functions()
        return self.__functions

    @property
    def nested_functions(self):
        funcs = dict(self.functions)
        for n, f in self.functions.items():
            funcs.update(self.__class__(f).nested_functions)
        return funcs


def locals_from_function(fn):
    return LocalsExtractor(fn).functions


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

