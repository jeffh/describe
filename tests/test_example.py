from describe import Value

def test_value():
    Value(5.0-4.0).should.be_close_to(1.0)
    Value((2,3,4)).should.contain(3)
    Value((2,3,4)).should_not.contain(5)
    Value(()).should.be.false()
    
    Value(range(5)).should.have.at_least(2).items
    
    Value(range(5)).should.have(5).items
    
def test_str():
    Value("Hello World").should.match(r"ello")
    
def test_operators():
    (Value(5) + 7).should == 12
    
def test_dict():
    Value(()).should.be.instance_of(tuple)