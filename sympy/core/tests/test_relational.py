from sympy import symbols, oo, Interval, solve, Rational
from sympy.core.relational import Relational, Equality, StrictInequality, \
    Rel, Eq, Lt, Le, Gt, Ge, Ne

x,y,z = symbols('xyz')


def test_rel_ne():
    Relational(x, y, '!=')  # this used to raise


def test_rel_subs():
    e = Relational(x, y, '==')
    e = e.subs(x,z)

    assert isinstance(e, Equality)
    assert e.lhs == z
    assert e.rhs == y

    e = Relational(x, y, '<')
    e = e.subs(x,z)

    assert isinstance(e, StrictInequality)
    assert e.lhs == z
    assert e.rhs == y


def test_wrappers():
    e = x+x**2

    res = Relational(y, e, '==')
    assert Rel(y, x+x**2, '==') == res
    assert Eq(y, x+x**2) == res

    res = Relational(y, e, '<')
    assert Lt(y, x+x**2) == res

    res = Relational(y, e, '<=')
    assert Le(y, x+x**2) == res

    res = Relational(y, e, '>')
    assert Gt(y, x+x**2) == res

    res = Relational(y, e, '>=')
    assert Ge(y, x+x**2) == res

    res = Relational(y, e, '!=')
    assert Ne(y, x+x**2) == res

def test_Eq():

    assert Eq(x**2) == Eq(x**2, 0)
    assert Eq(x**2) != Eq(x**2, 1)

def test_rel_Infinity():
    assert (oo > oo) is False
    assert (oo > -oo) is True
    assert (oo > 1) is True
    assert (oo < oo) is False
    assert (oo < -oo) is False
    assert (oo < 1) is False
    assert (oo >= oo) is True
    assert (oo >= -oo) is True
    assert (oo >= 1) is True
    assert (oo <= oo) is True
    assert (oo <= -oo) is False
    assert (oo <= 1) is False
    assert (-oo > oo) is False
    assert (-oo > -oo) is False
    assert (-oo > 1) is False
    assert (-oo < oo) is True
    assert (-oo < -oo) is False
    assert (-oo < 1) is True
    assert (-oo >= oo) is False
    assert (-oo >= -oo) is True
    assert (-oo >= 1) is False
    assert (-oo <= oo) is True
    assert (-oo <= -oo) is True
    assert (-oo <= 1) is True

def test_rel_inequalities():
    assert solve (x**2 - 10 > 3 * x,x) == [ Interval(-oo,-2,True,True), Interval(5,oo,True,True)]
    #fails assert solve(x**4+4*x**3-12*x**2>0,x) == [ Interval(-oo,-6,True,False), Interval(2,oo,False,True)]
    assert solve(3*x**2 > 2*x + 11,x) == [Interval(-oo, Rational(1, 3) - 34**(Rational(1, 2))/3,True,True), Interval(Rational(1, 3) + 34**(Rational(1, 2))/3, oo,True,True)]
    #fails assert solve((x-3)/(x+2)>=0,x) == [ Interval(-oo,-2,True,True), Interval(3,oo,False,True)]
    #fails assert solve((x**2-3*x-10)/(x-1)<0,x) == [ Interval(-oo,-2,True,True), Interval(1,5,True,True)]
    #fails assert solve(2*x/(x+1)>=3) == [ Interval(-3,-1,False,True)]

