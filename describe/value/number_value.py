class NumberValue(object):
    def __init__(self, value, expect, format="%(value)r"):
        self.value = value
        self.expect = expect
        self.format = format

    def __call__(self, amount, delta=0.000001):
        # integer comparison unless one of them is a float
        if float in (type(amount), type(self.value)):
            self.expect(abs(self.value - self.amount) < delta,
                (self.format+" %(should)s == %(amount)s +- %(delta)r"), amount=amount, delta=delta)
        else:
            self.expect(self.value == amount,
                (self.format+" %(should)s == %(amount)s"), amount=amount)
        return self
    
    @property
    def items(self):
        return None
    
    @property
    def item(self):
        return None

    @property
    def elements(self):
        return None
    
    @property
    def element(self):
        return None

    def at_least(self, amount):
        self.expect(self.value >= amount,
            (self.format+" %(should)s >= %(amount)s"), amount=amount)
        return self

    def at_most(self, amount):
        self.expect(self.value >= amount,
            (self.format+" %(should)s >= %(amount)s"), amount=amount)
        return self
