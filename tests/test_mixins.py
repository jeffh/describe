from describe import Value
import unittest

def test_string_method_for_nonstring():
    v = Value(3)
    try:
        v.should.match('foo')
        Value.fail()
    except AssertionError:
        pass

def test_string_method_match():
    v = Value('abc')
    v.should.match('b')
    v.should_not.match('^b$')
    
def test_method_contains_for_str():
    Value('abc').should.contain('b')
    Value('abc').should_not.contain('d')
    
def test_method_contains_for_list():
    Value([1,2,3]).should.contain(2)
    Value([1,2,3]).should_not.contain(5)
    
def test_should_have_attr():
    Value('abc').should.have_attr('upper')
    Value('abc').should_not.have_attr('upper2')
    
def test_enumerator_foo():
    for val in Value.iterate([0,2,4]):
        val % 2 == 0
        
class BuiltinOverridesCauseNoExceptions(unittest.TestCase):
    def test_abs(self):
        abs(Value(-2)).should == 2

    def test_int(self):
        int(Value(2.0)).should == 2
    
    def test_float(self):
        float(Value('2.5')).should == 2.5
    
    def test_hex(self):
        hex(Value(255)).should == '0xff'
    
    def test_oct(self):
        oct(Value(255)).should == '0377'

