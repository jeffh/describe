import sys
import inspect

class Frame(object):
    def __init__(self, frame, code_context=None, index=None):
        self.name = frame.f_code.co_name
        self.filename = frame.f_code.co_filename
        self.line_number = frame.f_lineno
        self.code_context = code_context
        self.index = index or 0

    def __repr__(self):
        return "<Frame: %(name)s %(filename)s @ %(linum)d:%(index)d>" % {
            'name': self.name,
            'filename': self.filename,
            'linum': self.line_number,
            'index': self.index,
        }

def get_last_traceback():
    tb = sys.exc_info()[2]
    while tb:
        if not tb.tb_next:
            break
        tb = tb.tb_next
    return tb

def get_stack(traceback):
    stack = []
    f = traceback.tb_frame
    while f:
        stack.append(Frame(f))
        f = f.f_back
    stack.reverse()
    return stack

def get_current_stack():
    stack = []
    for frm, filename, linum, method, code_context, index in inspect.stack()[1:]:
        stack.append(Frame(frm, code_context, index))
    return stack
