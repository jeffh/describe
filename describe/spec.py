import unittest
from describe import repository
from describe import Mock
from functools import wraps

__ALL__ = ['Spec']

def fails_verification(func):
    """This indicates that the given expectation should fail the mock verification process.

    This is used for internal testing only.
    """
    def decorated(self):
        self.method_expects_fail = func.__name__
        return func(self)
    return wraps(func)(decorated)

class Spec(unittest.TestCase):
    """A subclass of unittest.TestCase which provides some feature specific to describe.

    And renames methods to a more behavior-driven name.
    """
    def __init__(self, *args, **kwargs):
        super(Spec, self).__init__(*args, **kwargs)
        self.repository = repository.Repository()

    # ===== virtual methods =====
    def before(self):
        pass

    def after(self):
        pass
    # ===== end virtual methods =====

    def Mock(self, klass=None):
        """Shortcut to creating a mock object, which registers to an internal repository managed by this Spec instance."""
        return Mock(klass, repository=self.repository)

    def setUp(self):
        self.method_expects_fail = None
        self.before()

    def tearDown(self):
        if self.method_expects_fail:
            raised = None
            try:
                self.repository.verify()
                repository.default.verify()
            except AssertionError, e:
                raised = e
            method = getattr(self, self.method_expects_fail, self.method_expects_fail)
            message = "Expected AssertionError in %(name)s. Got %(error)r." % {
                'error': raised,
                'name': getattr(method, '__doc__', method) or self.method_expects_fail,
            }
            assert raised is not None, message
        else:
            self.repository.verify()
            repository.default.verify()
        self.after()
