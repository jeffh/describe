from describe import *
from sample import Bowling

class DescribeBowling(Spec):
    def it_returns_0_for_all_gutter_game(self):
        b = Bowling()
        for i in range(20):
            b.hit(0)
        Value(b.score).should == 0
    
    def it_should_throw_an_exception_on_crash(self):
        b = Bowling()
        Value(b).invoke.crash().should.raise_error(Exception)
        
if __name__ == '__main__':
    run_spec((DescribeBowling,))