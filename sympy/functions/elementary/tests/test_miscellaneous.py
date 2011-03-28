from sympy import oo, S
from sympy.core.symbol import Symbol
from sympy.functions.elementary.miscellaneous import Min, Max
from sympy.utilities.pytest import raises

def test_Min():
    from sympy.abc import x, y, z
    n = Symbol('n', negative=True)
    n_ = Symbol('n_', negative=True)
    nn = Symbol('nn', nonnegative=True)
    nn_ = Symbol('nn_', nonnegative=True)
    p = Symbol('p', positive=True)
    p_ = Symbol('p_', positive=True)
    np = Symbol('np', nonpositive=True)
    np_ = Symbol('np_', nonpositive=True)

    assert Min(5, 4) == 4
    assert Min(-oo, -oo) == -oo
    assert Min(-oo, n) == -oo
    assert Min(n, -oo) == -oo
    assert Min(-oo, np) == -oo
    assert Min(np, -oo) == -oo
    assert Min(-oo, 0) == -oo
    assert Min(0, -oo) == -oo
    assert Min(-oo, nn) == -oo
    assert Min(nn, -oo) == -oo
    assert Min(-oo, p) == -oo
    assert Min(p, -oo) == -oo
    assert Min(-oo, oo) == -oo
    assert Min(oo, -oo) == -oo
    assert Min(n, n) == n
    assert Min(n, np) == Min(n, np)
    assert Min(np, n) == Min(np, n)
    assert Min(n, 0) == n
    assert Min(0, n) == n
    assert Min(n, nn) == n
    assert Min(nn, n) == n
    assert Min(n, p) == n
    assert Min(p, n) == n
    assert Min(n, oo) == n
    assert Min(oo, n) == n
    assert Min(np, np) == np
    assert Min(np, 0) == np
    assert Min(0, np) == np
    assert Min(np, nn) == np
    assert Min(nn, np) == np
    assert Min(np, p) == np
    assert Min(p, np) == np
    assert Min(np, oo) == np
    assert Min(oo, np) == np
    assert Min(0, 0) == 0
    assert Min(0, nn) == 0
    assert Min(nn, 0) == 0
    assert Min(0, p) == 0
    assert Min(p, 0) == 0
    assert Min(0, oo) == 0
    assert Min(oo, 0) == 0
    assert Min(nn, nn) == nn
    assert Min(nn, p) == Min(nn, p)
    assert Min(p, nn) == Min(p, nn)
    assert Min(nn, oo) == nn
    assert Min(oo, nn) == nn
    assert Min(p, p) == p
    assert Min(p, oo) == p
    assert Min(oo, p) == p
    assert Min(oo, oo) == oo

    assert Min(n, n_).func is Min
    assert Min(nn, nn_).func is Min
    assert Min(np, np_).func is Min
    assert Min(p, p_).func is Min

    # lists

    raises(ValueError, 'Min()')
    assert Min(p, oo, n,  p, p, p_) == n
    assert set(Min(n, oo, -7, p,  p, 2).args) == set([n, S(-7)])
    assert set(Min(2, x, p, n, oo, n_,  p, 2, -2, -2).args) == set([S(-2), x, n, n_])
    assert set(Min(0, x, 1, y).args) == set([S(0), x, y])
    assert set(Min(1000, 100, -100, x, p, n).args) == set ([n, x, S(-100)])

def test_Max():
    from sympy.abc import x, y, z
    n = Symbol('n', negative=True)
    n_ = Symbol('n_', negative=True)
    nn = Symbol('nn', nonnegative=True)
    nn_ = Symbol('nn_', nonnegative=True)
    p = Symbol('p', positive=True)
    p_ = Symbol('p_', positive=True)
    np = Symbol('np', nonpositive=True)
    np_ = Symbol('np_', nonpositive=True)

    assert Max(5, 4) == 5

    # lists

    raises(ValueError, 'Max()')
    assert set(Max(n, -oo, n_,  p, 2).args) == set([p, S(2)])
    assert Max(n, -oo, n_,  p) == p
    assert set(Max(2, x, p, n, -oo, n_,  p, 2).args) == set([S(2), x, p])
    assert set(Max(0, x, 1, y).args) == set([S(1), x, y])
    assert Max(x, x + 1, x - 1) == 1 + x
    assert set(Max(1000, 100, -100, x, p, n).args) == set ([p, x, S(1000)])
    # interesting:
    # Max(n, -oo, n_,  p, 2) == Max(p, 2)
    # True
    # Max(n, -oo, n_,  p, 1000) == Max(p, 1000)
    # False


