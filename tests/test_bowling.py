from describe import *
import unittest
from bowling import Bowling

class TestBowling(unittest.TestCase):
    def test_change_value(self):
        b = Bowling()
        @Value
        def hit():
            b.hit(6)
        hit.should.change(b, 'hits').by(1)
        
    def test_change_value_increment(self):    
        s = {'a': 0}
        @Value
        def increment():
            s['a'] += 1
        increment.should.change(s, key='a').by(1)
        
    def test_return_value(self):
        b = Bowling()
        Value(b).invoke.foobar(9).return_value.should == 9
        
    def test_hit(self):
        b = Bowling()
        Value(b).invoke.hit(4).should_not.raise_error(Exception)
    
    def test_change_value_from_and_to(self):
        b = Bowling()
        @Value
        def hit():
            b.hit(6)
        hit.should.change(lambda: b.score).starting_from(0).to(6)
        
    def test_bowling_example(self):
        b = Bowling()
        for i in range(10):
            b.hit(0)
        Value(b.score).should == 0
        Value(b.score).should_not == 1
        Value(b).get.score.should == 0
        
    def test_bowling_all_9s_should_be_90(self):
        b = Bowling()
        for i in range(10):
            b.hit(9)
        Value(b.score).should == 90

        v = Value(2)
        v += 2
        v.should == 4
        
    def test_exceptions(self):
        b = Value(Bowling())
        b.invoke.crash().should.raise_error(Exception, "Implemented")
        b.invoke.crash().should_not.raise_error(TypeError)
        
        crash = b.invoke.crash()
        @crash.should.raise_error(Exception)
        def handle_exception(exception):
            Value(exception.message).should == "Not Implemented"
            
    def text_no_exceptions(self):
        b = Value(Bowling())
        b.invoke.crash().should_not.raise_error(TypeError)
        
    def test_satisfy(self):
        b = Value(Bowling())
        @b.should.satisfy
        def starting_score_should_be_zero(b):
            return b.score == 0

    def test_satisfy_lambda(self):
        b = Value(Bowling())
        b.should.satisfy(lambda b: b.score == 0)