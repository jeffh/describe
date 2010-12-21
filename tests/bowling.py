
class Bowling(object):
    def __init__(self):
        self.hits = 0
        self.score = 0
    
    def hit(self, value=0):
        self.hits += 1
        self.score += value
    
    def foobar(self, value=9):
        return value
        
    def crash(self):
        raise Exception, "Not Implemented"
        
    def __add__(self, other):
        b = Bowling()
        b.score = self.score + other
        return b
