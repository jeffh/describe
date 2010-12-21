import sys

class Frame(object):
    def __init__(self, frame):
        self.name = frame.f_code.co_name
        self.filename = frame.f_code.co_filename
        self.line_number = frame.f_lineno

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