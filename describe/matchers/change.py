from describe.matchers.core import MatcherBase, matcher_repository

class Tracker(object):
    "Verifies input provided via Changes class."
    def __init__(self, obj, name, invoke, expect, message=''):
        self.obj, self.name, self.invoke, self.expect = obj, name, invoke, expect
        self.message = message
        self.original_value = self.get_value()
        self.verifiers = []

    def get_value(self):
        value = getattr(self.obj, self.name)
        if self.invoke:
            return value()
        return value

    def get_postfix_message(self, actual_value):
        return ('change %(name)r ' + self.message) % {
            'name': self.name,
            'old': self.original_value,
            'new': self.new_value,
        }

    def add_verifier(self, fn):
        self.verifiers.append(fn)
        return self

    def __enter__(self):
        return self.obj

    def __exit__(self, type, value, exception):
        # verify
        self.new_value = new_value = self.get_value()
        if not len(self.verifiers):
            raise TypeError("You must specify changes to this value (use by or to methods)")
        for verify in self.verifiers:
            self.expect(verify(self.original_value, new_value), self)

class Changes(object):
    "Receives testing input from the user."
    UNSET = object()
    def __init__(self, obj, name, invoke, expect):
        self.obj, self.name, self.invoke, self.expect = obj, name, invoke, expect
        self.expected_original_value = self.UNSET

    def by(self, amount):
        def verify_change(old_value, new_value):
            return new_value - old_value == amount
        message = ('from %d ' % self.expected_original_value if self.has_starting_value else '') + ('by %s' % amount)
        return self.add_starting_value_verifier(
            Tracker(self.obj, self.name, self.invoke, self.expect, message).add_verifier(verify_change)
        )

    def by_at_least(self, amount):
        def verify_change(old_value, new_value):
            return new_value - old_value >= amount
        message = ('from %d ' % self.expected_original_value if self.has_starting_value else '')
        message += 'by at least %s' % amount
        return self.add_starting_value_verifier(
            Tracker(self.obj, self.name, self.invoke, self.expect, message).add_verifier(verify_change)
        )

    def by_at_most(self, amount):
        def verify_change(old_value, new_value):
            return new_value - old_value <= amount
        message = ('from %d ' % self.expected_original_value if self.has_starting_value else '')
        message += 'by at most %d' % amount
        return self.add_starting_value_verifier(
            Tracker(self.obj, self.name, self.invoke, self.expect, message).add_verifier(verify_change)
        )

    def starting_from(self, start_value):
        self.expected_original_value = start_value
        return self

    def add_starting_value_verifier(self, tracker):
        if self.expected_original_value is self.UNSET:
            return tracker

        def verify_starting_value(old_value, new_value):
            return old_value == self.expected_original_value

        tracker.add_verifier(verify_starting_value)
        return tracker

    @property
    def has_starting_value(self):
        return self.expected_original_value is not self.UNSET

    def to(self, end_value):
        def verify_ending_value(old_value, new_value):
            return new_value == end_value

        message = ('from %d ' % self.expected_original_value if self.has_starting_value else '') + ' to %(new)r'
        tracker = Tracker(self.obj, self.name, self.invoke, self.expect, message)
        return self.add_starting_value_verifier(tracker.add_verifier(verify_ending_value))

class ToChangeMatcher(MatcherBase):
    METHODS = ['change']

    def __init__(self, value, invoke=False):
        super(ToChangeMatcher, self).__init__(value)
        self.invoke = False

    def get_postfix_message(self, actual_value):
        raise NotImplementedError()

    def asserts(self, obj, attrname):
        return Changes(obj.evaluate(), attrname, self.invoke, self._expect)

    def __enter__(self):
        raise TypeError('change needs additional methods to help verify (use by(change_amount) or to(final_value)')

    def __exit__(self, type, value, exception):
        pass

matcher_repository.add(ToChangeMatcher)
