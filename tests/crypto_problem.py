import utils

inf = float('inf')
s = {}

def extended_euclidean(a, b):
    x, lx, y, ly = 0, 1, 1, 0
    while b != 0:
        q = a // b
        a, b = b, a % b
        x, lx, y, ly = lx - q * x, x, ly - q * y, y
    return lx, ly, a


class Equation(object):
    def __init__(self, x, y, mod=1000, a=1):
        self._x, self._y, self._a = x, y, a
        self._mod = mod
    
    def div(self, a, b):
        return (a * (extended_euclidean(b, self._mod)[0] % self._mod)) % self._mod
    
    def m(self, p1, p2):
        x1,y1 = p1
        x2,y2 = p2
        if p1 == p2:
            if y1 == 0:
                return inf
            return self.div((3*(x1**2) + self._a), (2 * y1))
        if x2 - x1 == 0:
            return inf
        return self.div(y2-y1, x2-x1)
        
    def find_maximum_order(self):
        points = self.get_all()
        maximum_order = 0
        maximum_points = []
        
        
        for pt in points:
            visited = set([(inf, inf)])
            p = pt
            c = 1
            while p not in visited:
                visited = visited.union([p])
                p = self.add_points(p, pt)
                c += 1
            if c > maximum_order:
                maximum_order = c
                maximum_points = [pt]
            elif c == maximum_order:
                maximum_points.append(pt)
        return maximum_points, maximum_order
        
    def add_points(self, pt1, pt2):
        x1, y1 = pt1
        x2, y2 = pt2
        x3 = self.m(pt1, pt2) ** 2 - x1 - x2
        y3 = self.m(pt1, pt2) * (x1 - x3) - y1
        if x3 == inf or y3 == inf:
            return (inf, inf)
        return (x3, y3)
        
    def get_y(self, x):
        ax = self._x(x) % self._mod
        answers = []
        for yi in range(self._mod):
            a = self._y(yi) % self._mod
            if a == ax:
                answers.append((x, yi))
        return set(answers)
        
    def get_all(self):
        answers = [(inf, inf)]
        for xi in range(self._mod):
            answers.extend(self.get_y(xi))
        return set(answers)
        
    def get_all_qrs(self):
        answers = [(inf, inf)]
        for (x, y) in self.get_all():
            if utils.L(y**2, self._mod) == 1:
                answers.append((x,y))
        return set(answers)

if __name__ == '__main__':
    eq = Equation(x=lambda a: a**3 + a + 28, y=lambda a: a**2, mod=71, a=1)
    print len(eq.get_all())
    print eq.find_maximum_order()
