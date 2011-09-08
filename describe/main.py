import sys
import nose

from nose_plugin import SpecPlugin
from tracebacks import get_last_traceback, get_stack

def run_spec(specs=()):
    for spec_class in specs:
        spec = spec_class()
        set_up = getattr(spec, 'before', None)
        tear_down = getattr(spec, 'after', None)
        for name in spec_class.__dict__.keys():
            if not name.startswith('it'):
                continue
            if set_up:
                set_up()
            try:
                getattr(spec, name)()
                sys.stdout.write('.')
            except AssertionError, ae:
                tb = get_last_traceback()
                stack = get_stack(tb)

                for frame in stack:
                    print "Frame: %s in %s at line %s:" % (
                        frame.name,
                        frame.filename,
                        frame.line_number,
                    )
                sys.stdout.write('E')
            finally:
                if tear_down:
                    tear_down()
                sys.stdout.flush()

if __name__ == '__main__':
    #nose.main(addplugins=[SpecPlugin()])
    nose.run(addplugins=[SpecPlugin()])
