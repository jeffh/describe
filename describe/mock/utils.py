import types

from describe.flags import is_flag

def is_function(value):
    return type(value) == types.FunctionType

TWO_OPS = 'or add sub mul floordiv divmod lshift rshift and xor div truediv pow mod'.split(' ')
TWO_OPS_FULL = TWO_OPS + ['r' + o for o in TWO_OPS] + ['i' + o for o in TWO_OPS]
ONE_OPS = 'neg pos abs invert enter exit eq ne'.split(' ')

class NILObject(object):
	pass

NIL = NILObject


def get_args_str(args, kwargs):
	args = []
	if args and not is_flag(args):
		args += [repr(a) for a in args]
	if kwargs and not is_flag(kwargs):
		for k, v in kwargs.items():
			args.append('%s=%r' % (k, v))
	return ', '.join(args)
