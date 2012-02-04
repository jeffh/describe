import types
import traceback
import inspect
import time
from functools import wraps, partial

import byteplay


def filter_traceback(error, tb, CONST='__DESCRIBE_FRAME_MARK'):
    """Filtered out all parent stacktraces starting with the given stacktrace that has
    a given variable name in its globals.
    """
    if not isinstance(tb, types.TracebackType):
        return tb
    # Skip test runner traceback levels
    while tb and CONST in tb.tb_frame.f_globals:
        tb = tb.tb_next

    return ''.join(traceback.format_exception(error.__class__, error, tb))


def with_metadata(decorator):
    """Creates a new decorator that records the function metadata on the generated
    decorated function.
    """
    @wraps(decorator)
    def new_decorator(func):
        decorated = decorator(func)
        # if the decorator is a "no-op", do nothing
        if not callable(decorator):
            return decorated
        # record data
        decorated.__decorator__ = decorator

        if isinstance(func, partial):
            # partials are objects that store the true function somewhere else
            decorated.__wraps__ = func.keywords['wrapped']
        else:
            decorated.__wraps__ = func
        return decorated

    return new_decorator


def returns_locals(func):
    """Modify the function to do:

        _________describe_exception = None
        try:
            # existing code
        except Exception, e:
            _________describe_exception = e
        finally:
            import sys
            if _________describe_exception:
                return sys.exc_info()
            return locals()

    We can't just return locals(), because exceptions will be absorbed then, but we need
    to return in the finally block to override any other possible returns the function
    does.
    """
    # we need to "unwrap" decorators. They need to be using the with_metadata
    # decorator
    f = func
    decorators = [f]
    wraps = getattr(f, '__wraps__', None)
    while callable(wraps):
        f = wraps
        decorators.append(f)
        wraps = getattr(f, '__wraps__', None)

    decorators.pop() # last function is the true function we're working on

    assert callable(f), "f must be a function"

    # if we already modified this function before, do nothing
    if getattr(f, '__returns_locals__', None):
        return (decorators and decorators[0]) or f

    fcode = f.func_code
    code = byteplay.Code.from_code(fcode)
    except_label, except_if_label = byteplay.Label(), byteplay.Label()
    finally_label, run_finally_label = byteplay.Label(), byteplay.Label()
    finally_if_label = byteplay.Label()

    code.code = (
        [
            (byteplay.LOAD_GLOBAL, 'None'),
            (byteplay.STORE_FAST, '_________describe_exception'),
            (byteplay.SETUP_FINALLY, run_finally_label),
            (byteplay.SETUP_EXCEPT, except_label),
        ]
        + code.code +
        [
            (byteplay.POP_BLOCK, None),
            (byteplay.JUMP_FORWARD, finally_label),
            (except_label, None),
            #(byteplay.SetLineno, 5),
            (byteplay.DUP_TOP, None),
            (byteplay.LOAD_GLOBAL, 'Exception'),
            (byteplay.COMPARE_OP, 'exception match'),
            (byteplay.POP_JUMP_IF_FALSE, except_if_label),
            (byteplay.POP_TOP, None),
            (byteplay.STORE_FAST, 'e'),
            (byteplay.POP_TOP, None),
            #(byteplay.SetLineno, 6),
            (byteplay.LOAD_FAST, 'e'),
            (byteplay.STORE_FAST, '_________describe_exception'),
            (byteplay.JUMP_FORWARD, finally_label),
            (except_if_label, None),
            (byteplay.END_FINALLY, None),
            (finally_label, None),
            (byteplay.POP_BLOCK, None),
            (byteplay.LOAD_CONST, None),
            (run_finally_label, None),
            #(byteplay.SetLineno, 8),
            (byteplay.LOAD_CONST, -1),
            (byteplay.LOAD_CONST, None),
            (byteplay.IMPORT_NAME, 'sys'),
            (byteplay.STORE_FAST, 'sys'),
            #(byteplay.SetLineno, 9),
            (byteplay.LOAD_FAST, '_________describe_exception'),
            (byteplay.POP_JUMP_IF_FALSE, finally_if_label),
            #(byteplay.SetLineno, 10),
            (byteplay.LOAD_FAST, 'sys'),
            (byteplay.LOAD_ATTR, 'exc_info'),
            (byteplay.CALL_FUNCTION, 0),
            (byteplay.RETURN_VALUE, None),
            (byteplay.JUMP_FORWARD, finally_if_label),
            (finally_if_label, None),
            #(byteplay.SetLineno, 11),
            (byteplay.LOAD_GLOBAL, 'locals'),
            (byteplay.CALL_FUNCTION, 0),
            (byteplay.RETURN_VALUE, None),
            (byteplay.END_FINALLY, None),
        ])
    f.func_code = code.to_code()

    # tag the function, to prevent use from modifying it again
    f.__returns_locals__ = True

    return (decorators and decorators[0]) or f


def locals_from_function(fn):
    localfn = returns_locals(fn)
    context = localfn()
    if isinstance(context, dict) and '_________describe_exception' in context:
        del context['_________describe_exception']
        del context['sys']
        return {name: value for name, value in context.items() if callable(value)}

    # else we got an exception
    raise context[0], context[1], context[2]


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

    def __call__(self, func):
        def decorator(fn):
            @wraps(fn)
            def decorated(*args, **kwargs):
                with self as obj:
                    return fn(obj, *args, **kwargs)
            return decorated
        return with_metadata(decorator)(func)


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

