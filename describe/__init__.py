from describe.meta import *
from describe.wrappers import Expectation as expect
from describe.mock import Stub, patch
from describe.matchers import matcher
from describe.spec.utils import with_metadata
import describe.flags as flags
from describe.mock.consumers import *

def main():
    from describe.main import main as entry_point
    import sys
    sys.exit(entry_point(*sys.argv))
