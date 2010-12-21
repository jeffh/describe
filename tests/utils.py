import random

def L(a, p):
    """The legendre symbol function.
    This only works if p is an odd prime.
    
    Returns 1 if a is in the Quadratic Residue of p. -1 if in QNR of p. 0 otherwise.
    """
    if a % p == 0:
        return 1
    apow = a ** ((p-1)/2)
    if (apow - 1) % p == 0:
        return 1
    if (apow + 1) % p == 0:
        return -1


def J(x, p):
    """The jacobi symbol function.
    """
    # property 1
    if p % 2 != 0 and x >= p: # not recursive to save stack frames
        x = x % p
    # property 2
    if x == 2:
        if (p + 1) % 8 == 0 or (p - 1) % 8 == 0:
            return 1
        if (p + 3) % 8 == 0 or (p - 3) % 8 == 0:
            return -1
    # property 3
    c = 0
    tmp = x
    while tmp % 2 == 0 and tmp != 0:
        c += 1
        tmp /= 2
    if c > 0 and tmp % 2 != 0:
        return J(2, p) ** c * J(tmp, p)
    # property 4
    if x % 2 != 0 and p % 2 != 0:
        if (x - 3) % 4 == (p - 3) % 4 == 0:
            return -J(p, x)
        else:
            return J(p, x)
    return 1

def gcd(a, b):
    while b != 0:
        a, b = b, a % b
    return a

def extended_euclidean(a, b):
    x, lx, y, ly = 0, 1, 1, 0
    while b != 0:
        q = a // b
        a, b = b, a % b
        x, lx, y, ly = lx - q * x, x, ly - q * y, y
    return lx, ly, a
    

def is_prime(n):
    "A poorly implemented verification if n is prime."
    for i in range(2, n):
        if gcd(i, n) != 1:
            return False
    return True

def coprimes(n):
    """Returns an iterator of values less than, but coprime to n.

    This is the multiplicative group of the given prime?
    """
    for x in range(1, n):
        if gcd(x, n) == 1:
            yield x

def random_coprime(n, randchoice=random.choice):
    """Picks a random integer that is < n and is coprime to n.
    """
    return randchoice(list(coprimes(n)))

def totient(n):
    """
    Returns: the size of the reduced set of residues.
    """
    return len(list(coprimes(n)))
    
# function for computing the Legendre Symbol of x/p
# i've excluded the jacobi fucntion since it would require a prime factorization algorithm,
# which is, of course, a hard problem
def legendre(x,p):
    # establish the set of quadratic residues of p
    QRp = [(a**2)%p for a in range(1,((p-1)/2)+1)]
    
    if x%p in QRp: return 1
    else: return -1