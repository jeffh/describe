from describe import Value

def test_value():
    Value(5.0-4.0).should.be.close_to(1.0)
    Value(True).should_not.be.false()
    
    Value((2,3,4)).should.contain(3)
    Value((2,3,4)).should_not.contain(5)
    Value(()).should.be.false()
    
    Value(range(5)).should.have.at_least(2).items
    
    Value(range(5)).should.have(5).items
    
def test_str():
    Value("Hello World").should.match("ello")
    Value("Hello World").invoke.lower().should == "hello world"
    
def test_operators():
    (Value(5) + 7).should == 12
    Value(10).should.be <= 60 # be is optional
    Value(100).should > 20
    Value(50).should != 51
    
def test_dict():
    Value({}).should.be.instance_of(dict)
    # {'foo':'bar'}['foo']
    Value({'foo': 'bar'}).get['foo'].should == "bar"
    Value({}).get['foo'].should.raise_error(KeyError)
    Value({'foo': 'bar'}).get['foo'].should_not.raise_error(KeyError)
    # {}.get('foo', None)
    Value({}).invoke.get('foo', None).should == None