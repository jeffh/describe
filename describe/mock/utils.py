import types

def is_function(value):
    return type(value) == types.FunctionType

TWO_OPS = 'or add sub mul floordiv divmod lshift rshift and xor div truediv pow mod'.split(' ')
TWO_OPS_FULL = TWO_OPS + ['r' + o for o in TWO_OPS] + ['i' + o for o in TWO_OPS]
ONE_OPS = 'neg pos abs invert enter exit eq ne'.split(' ')

class NILObject(object):
	pass

NIL = NILObject

