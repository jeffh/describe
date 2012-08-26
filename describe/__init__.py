from describe.meta import *
from describe.wrappers import Expectation as expect
from describe.mock import *
from describe.matchers import matcher
from describe.utils import with_metadata
from describe import run
import describe.flags as flags

def main():
    from describe.main import main as entry_point
    import sys
    sys.exit(entry_point(*sys.argv))
