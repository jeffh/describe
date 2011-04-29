from describe import Value

def test_raise_exception():
    @Value
    def v():
        raise TypeError
        return False
    v().should.raise_error(TypeError)

def test_not_raising_exception():
    @Value
    def v():
        return True
    v().should_not.raise_error(TypeError)
    
class Example(object):
    def __init__(self, val):
        self.val = val
    
    def return_value(self):
        return self.val
    
    def throw_exception(self):
        raise TypeError, "Oh no"

def test_example_raising_exception():
    Value(Example(2)).invoking.throw_exception().should.raise_error(TypeError)
    
def test_example_not_raising_exception():
    Value(Example(2)).invoking.return_value().should_not.raise_error(TypeError)
    Value(Example(2)).invoking.return_value().should == 2