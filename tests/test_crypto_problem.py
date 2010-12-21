from describe import Value
from crypto_problem import *

def test_ec():
    e = Value(Equation(x=lambda a: a**3 + 2 * a - 1, y=lambda b: b**2, mod=5))
    e.invoke.get_y(x=0).should == set([(0,2), (0,3)])
    e.invoke.get_y(x=2).should == set([(2,1), (2,4)])
    e.invoke.get_y(x=4).should == set([(4,1), (4,4)])
    
    
    e.invoke.get_all().should == set([(0,2), (0,3), (2,1), (2,4), (4,1), (4,4), (inf, inf)])
    
def test_qrs():
    e = Value(Equation(x=lambda a: a**3 + a + 6, y=lambda b: b**2, mod=11))
    e.invoke.get_all_qrs().should == set([
        (2,4), (2,7),
        (3,5), (3,6),
        (5,2), (5,9),
        (7,2), (7,9),
        (8,3), (8,8),
        (10,2), (10,9),
        (inf, inf)
    ])
    
def test_qrs2():
    e = Value(Equation(x=lambda a: a**3 + 4*a - 1, y=lambda b: b**2, mod=5))
    e.invoke.get_all().should == set([
        (0,2), (0,3),
        (1,2), (1,3),
        (2,0),
        (4,2), (4,3),
        (inf, inf),
    ])
    e.invoke.get_all_qrs().should == set([
        (0,2), (0,3),
        (1,2), (1,3),
        (2,0),
        (4,2), (4,3),
        (inf, inf),
    ])