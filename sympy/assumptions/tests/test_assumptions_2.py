"""rename this to test_assumptions.py when the old assumptions system is deleted"""
from sympy.core import symbols
from sympy.assumptions import (Assume, get_local_assumptions,
    set_local_assumptions, ask, Q, Predicate, AssumptionsContext)
from sympy.assumptions.assume import eliminate_assume
from sympy.printing import pretty
from sympy.utilities.pytest import XFAIL

def test_assume():
    x = symbols('x')
    assump = Assume(x, 'integer')
    assert assump.expr == x
    assert assump.key == Q.integer

def test_Predicate_wraps_Assume():
    x = symbols('x')
    integer = Predicate('integer')
    assump = integer(x)
    assert (assump.expr, assump.key) == (x, integer)
    assump = Assume(x, integer)
    assert (assump.expr, assump.key) == (x, integer)

def test_False():
    """Test Assume object with False keys"""
    x = symbols('x')
    assump = Assume(x, 'integer', False)
    assert assump == ~Assume(x, 'integer')


def test_equal():
    """Test for equality"""
    x = symbols('x')
    assert Assume(x, 'positive', True)  == Assume(x, 'positive', True)
    assert Assume(x, 'positive', True)  != Assume(x, 'positive', False)
    assert Assume(x, 'positive', False) == Assume(x, 'positive', False)

@XFAIL #TODO: handle printing
def test_pretty():
    x = symbols('x')
    assert pretty(Assume(x, 'positive')) == "Assume(x, 'positive')"

def test_eliminate_assumptions():
    a, b = map(Predicate, symbols('ab'))
    x, y = symbols('xy')
    assert eliminate_assume(Assume(x, a))  == a
    assert eliminate_assume(Assume(x, a), symbol=x)  == a
    assert eliminate_assume(Assume(x, a), symbol=y)  == None
    assert eliminate_assume(Assume(x, a, False)) == ~a
    assert eliminate_assume(Assume(x, a), symbol=y) == None
    assert eliminate_assume(Assume(x, a) | Assume(x, b)) == a | b
    assert eliminate_assume(Assume(x, a) | Assume(x, b, False)) == a | ~b

def test_context():
    x, y = symbols('x y')
    a = AssumptionsContext()
    a.add(Assume(x>0))
    assert Assume(x>0) in a
    a.remove(Assume(x>0))
    assert not Assume(x>0) in a
    # multiple assumptions
    a.add(Assume(x>0), Assume(y>0))
    assert Assume(x>0) in a
    assert Assume(y>0) in a
    a.clear()
    assert not Assume(x>0) in a
    assert not Assume(y>0) in a
    # And, Or, Not can also be added
    a.add(~Assume(x, Q.positive))
    a.add(Assume(y, Q.even) & Assume(y, Q.positive))
    a.add(Assume(x + y, Q.positive) | Assume(x - y, Q.negative))

def test_local():
    x, y = symbols('x y')
    set_local_assumptions()
    a = get_local_assumptions()
    a.add(Assume(x, Q.positive))
    def localfunc():
        assert Assume(x, Q.positive) in get_local_assumptions()
        assert ask(x, Q.positive) == True
        b = set_local_assumptions()
        assert not b is a
        b.add(Assume(x, Q.negative))
        assert ask(x, Q.positive) == False
    localfunc()
    assert a
    assert ask(x, Q.positive) == True
