from number_value import NumberValue

class ChangeValue(object):
    """A specific value implementation for spec-ing change in numbers.

    Represents a change in value by Value.should.change attribute.
    """
    def __init__(self, obj, expect, attr=None, key=None):
        self.obj, self.attr, self.key = obj, attr, key
        self.type = type(obj)
        self.old, self.new = self.capture_value(), None
        # remember, expect's value is the dirty function that was invoked
        self.expect = expect

    # internal -- some are used by Value instance that created us
    @property
    def attr_name(self):
        if callable(self.obj) and self.attr is None:
            return "%s" % (self.obj.__name__)
        return "%s.%s" % (self.type.__name__, self.attr)

    def capture_value(self):
        if callable(self.obj) and self.attr is None:
            return self.obj()
        if self.attr:
            return getattr(self.obj, self.attr)
        if self.key:
            return self.obj[self.key]

    def capture_value_as_new(self):
        self.new = self.capture_value()

    def expect_values_to_be_not_equal(self):
        self.expect(self.old != self.new,
            "%(value_name)s %(should)s change %(target)s",
            target=self.attr_name)

    def expect_values_to_be_equal(self):
        self.expect(self.old == self.new,
            "%(value_name)s %(should)s change %(target)s",
            target=self.attr_name)
    # end internal

    @property
    def by(self):
        """Returns a NumberValue of the change for comparison.

        Since the NumberValue can be called on like a function, you can do:
        chgValue.by(5) # => difference should equal 5
        """
        return NumberValue(abs(self.old - self.new), self.expect,
            format="abs("+str(self.old)+" - "+str(self.new)+") = %(value)r")

    def starting_from(self, value):
        self.expect(self.old == value,
            "%(value_name)s %(should)s start from %(expected)r, instead of %(old)r, at %(target)s",
            target=self.attr_name, expected=value, old=self.old)
        return self

    def to(self, value):
        self.expect(self.new == value,
            "%(value_name)s %(should)s become %(expected)r," +
            " instead of %(new)r, at %(target)s",
            target=self.attr_name, expected=value, new=self.new)
        return self
