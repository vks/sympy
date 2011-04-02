from sympy import Lambda, Symbol, Function, Derivative, sqrt, \
        log, exp, Rational, Real, sin, cos, diff, I, re, im, \
        oo, zoo, nan, E, expand, pi, O, Sum, S
from sympy.utilities.pytest import XFAIL, raises
from sympy.abc import x, y
from sympy.core.function import PoleError

def test_f_expand_complex():
    f = Function('f')
    x = Symbol('x', real=True)
    z = Symbol('z')

    assert f(x).expand(complex=True)        == I*im(f(x)) + re(f(x))
    assert exp(x).expand(complex=True)      == exp(x)
    assert exp(I*x).expand(complex=True)    == cos(x) + I*sin(x)
    assert exp(z).expand(complex=True)      == cos(im(z))*exp(re(z)) + \
                                             I*sin(im(z))*exp(re(z))

def test_bug1():
    x = Symbol("x")
    w = Symbol("w")

    e = sqrt(-log(w))
    assert e.subs(log(w),-x) == sqrt(x)

    e = sqrt(-5*log(w))
    assert e.subs(log(w),-x) == sqrt(5*x)

def test_general_function():
    nu = Function('nu', nargs=1)
    x = Symbol("x")
    y = Symbol("y")

    e = nu(x)
    edx = e.diff(x)
    edy = e.diff(y)
    edxdx = e.diff(x).diff(x)
    edxdy = e.diff(x).diff(y)
    assert e == nu(x)
    assert edx != nu(x)
    assert edx == diff(nu(x), x)
    assert edy == 0
    assert edxdx == diff(diff(nu(x), x), x)
    assert edxdy == 0

def test_function_nargs():
    f = Function('f')
    x = Symbol('x')
    assert f.nargs == None
    assert f(x).nargs == 1
    assert f(x, x, x, x).nargs == 4

def test_derivative_subs_bug():
    x = Symbol("x y")
    l = Function('l', nargs=1)
    n = Function('n', nargs=1)

    e = diff(n(x), x)
    assert e.subs(n(x), l(x)) != e
    assert e.subs(n(x), l(x)) == Derivative(l(x), x)
    assert e.subs(n(x), -l(x)) == Derivative(-l(x), x)

    assert e.subs(x, y) == Derivative(n(y), y)

def test_derivative_subs_self_bug():
    f = Function('f')
    d = diff(f(x), x)

    assert d.subs(d, y) == y


def test_derivative_linearity():
    x = Symbol("x")
    y = Symbol("y")
    n = Function('n', nargs=1)

    assert diff(-n(x), x) == -diff(n(x), x)
    assert diff(8*n(x), x) == 8*diff(n(x), x)
    assert diff(8*n(x), x) != 7*diff(n(x), x)
    assert diff(8*n(x)*x, x) == 8*n(x) + 8*x*diff(n(x), x)
    assert diff(8*n(x)*y*x, x) == 8*y*n(x) + 8*y*x*diff(n(x), x)

def test_derivative_evaluate():
    x = Symbol('x')

    assert Derivative(sin(x), x) != diff(sin(x), x)
    assert Derivative(sin(x), x).doit() == diff(sin(x), x)

    f = Function('f')
    assert Derivative(Derivative(f(x), x), x) == diff(f(x), x, x)
    assert Derivative(sin(x), x, 0) == sin(x)

def test_diff_symbols():
    x = Symbol('x')
    y = Symbol('y')
    z = Symbol('z')
    f = Function('f')

    assert diff(f(x, y, z), x, y, z) == Derivative(f(x, y, z), x, y, z)
    assert diff(f(x, y, z), x, x, x) == Derivative(f(x, y, z), x, x, x)
    assert diff(f(x, y, z), x, 3) == Derivative(f(x, y, z), x, 3)

    # issue 1929
    assert [diff(-z + x/y, sym) for sym in (z, x, y)] == [-1, 1/y, -x/y**2]
    assert diff(f(x, y, z), x, y, z, 2) == Derivative(f(x, y, z), x, y, z, z)
    assert diff(f(x, y, z), x, y, z, 2, evaluate=False) == \
        Derivative(f(x, y, z), x, y, z, z)
    assert Derivative(f(x, y, z), x, y, z)._eval_derivative(z) == \
        Derivative(f(x, y, z), x, y, z, z)
    assert Derivative(Derivative(f(x, y, z), x), y)._eval_derivative(z) == \
        Derivative(f(x, y, z), x, y, z)

def test_Lambda():
    e = Lambda(x, x**2)
    f = Function('f')
    assert e(4) == 16
    assert e(x) == x**2
    assert e(y) == y**2

    assert Lambda(x, x**2) == Lambda(x, x**2)
    assert Lambda(x, x**2) == Lambda(y, y**2)
    assert Lambda(x, x**2) != Lambda(y, y**2+1)
    assert Lambda(x,y,x**y) == Lambda(y,x,y**x)
    assert Lambda(x,y,x**y) != Lambda(x,y,y**x)

    assert Lambda(x,y,x**y)(x,y) == x**y
    assert Lambda(x,y,x**y)(x) == Lambda(y,x**y)
    assert Lambda(x,y,x**y)(x)(y) == x**y
    assert Lambda(x,y,x**y)(x)(3) == x**3
    assert Lambda(x,y,x**y)(3)(y) == 3**y
    assert Lambda(x,y,x**y)(3)(3) == 3**3
    assert Lambda(x,y,x**y)(3,3) == 3**3
    assert Lambda(x,y,x**y)(x,3) == x**3
    assert Lambda(x,y,x**y)(3,y) == 3**y
    assert Lambda(x,f(x))(x) == f(x)
    assert Lambda(x,f(x))() == Lambda(x,f(x))
    assert Lambda(x,x**2)(e(x)) == x**4
    assert e(e(x)) == x**4
    assert Lambda(x,y,f(x)+f(y))(x) == Lambda(y,f(x)+f(y))
    #doesn't work yet:
    #class F(Function):
    #    pass
    #assert Lambda(x, F(x)) == F

    assert Lambda(x, y, x+y).nargs == 2

    z = Symbol('z')
    t = Symbol('t')
    p = x, y, z, t
    assert Lambda(p, t*(x+y+z))(*p) == t * (x + y + z)

def test_Lambda_is_identity():
    assert Lambda(x, x).is_identity == True
    assert Lambda(x, 2*x).is_identity == False
    assert Lambda((x, y), x).is_identity == None

def test_expand_function():
    assert expand(x+y) == x + y
    assert expand(x+y, complex=True) == I*im(x) + I*im(y) + re(x) + re(y)
    assert expand((x + y)**11, modulus=11) == x**11 + y**11

def test_function_comparable():
    x = Symbol('x')

    assert sin(x).is_comparable == False
    assert cos(x).is_comparable == False

    assert sin(Real('0.1')).is_comparable   == True
    assert cos(Real('0.1')).is_comparable   == True

    assert sin(E).is_comparable     == True
    assert cos(E).is_comparable     == True

    assert sin(Rational(1,3)).is_comparable == True
    assert cos(Rational(1,3)).is_comparable == True

@XFAIL
def test_function_comparable():
    assert sin(oo).is_comparable    == False
    assert sin(-oo).is_comparable   == False
    assert sin(zoo).is_comparable   == False
    assert sin(nan).is_comparable   == False

def test_deriv1():
    f=Function('f')
    g=Function('g')
    x = Symbol('x')
    # this is a place where the polys12 Pure() symbol could be used rather than unique dummies
    assert str(f(g(x)).diff(x)) == 'D(f(_u), _u)*D(g(x), x)'

def test_deriv2():
    f = Function('f')
    x = Symbol('x')

    assert f(x).diff(x) == Derivative(f(x), x)
    assert str(f(2*x).diff(x)) == '2*D(f(_u), _u)'
    assert (f(x)**3).diff(x) == 3*f(x)**2*f(x).diff(x)
    assert str((f(2*x)**3).diff(x)) == '6*f(2*x)**2*D(f(_u), _u)'

    assert str(f(2+x).diff(x)) == 'D(f(_u), _u)'
    assert str(f(2+3*x).diff(x)) == '3*D(f(_u), _u)'
    assert str(f(sin(x)).diff(x)) == 'D(f(_u), _u)*cos(x)'
    assert str(f(3*sin(x)).diff(x)) == '3*D(f(_u), _u)*cos(x)'

def test_deriv3():
    x = Symbol('x')

    assert (x**3).diff(x) == 3*x**2
    assert (x**3).diff(x, evaluate=False) != 3*x**2
    assert (x**3).diff(x, evaluate=False) == Derivative(x**3, x)

    assert diff(x**3, x) == 3*x**2
    assert diff(x**3, x, evaluate=False) != 3*x**2
    assert diff(x**3, x, evaluate=False) == Derivative(x**3, x)

def test_suppressed_evaluation():
    a = sin(0, evaluate=False)
    assert a != 0
    assert a.func is sin
    assert a.args == (0,)

def test_function_evalf():
    def eq(a,b,eps):
        return abs(a-b) < eps
    assert eq(sin(1).evalf(15), Real("0.841470984807897"), 1e-13)
    assert eq(sin(2).evalf(25), Real("0.9092974268256816953960199",25), 1e-23)
    assert eq(sin(1+I).evalf(15), Real("1.29845758141598") + Real("0.634963914784736")*I, 1e-13)
    assert eq(exp(1+I).evalf(15), Real("1.46869393991588") + Real("2.28735528717884239")*I, 1e-13)
    assert eq(exp(-0.5+1.5*I).evalf(15), Real("0.0429042815937374") + Real("0.605011292285002")*I, 1e-13)
    assert eq(log(pi+sqrt(2)*I).evalf(15), Real("1.23699044022052") + Real("0.422985442737893")*I, 1e-13)
    assert eq(cos(100).evalf(15), Real("0.86231887228768"), 1e-13)

def test_extensibility_eval():
    class MyFunc(Function):
        @classmethod
        def eval(cls, *args):
            return (0,0,0)
    assert MyFunc(0) == (0,0,0)

def test_function_non_commutative():
    x = Symbol('x', commutative=False)
    f = Function('f')
    assert f(x).is_commutative == False
    assert sin(x).is_commutative == False
    assert exp(x).is_commutative == False
    assert log(x).is_commutative == False

def test_function__eval_nseries():
    x = Symbol('x')
    assert sin(x)._eval_nseries(x,2) == x + O(x**2)
    assert sin(x+1)._eval_nseries(x,2) == x*cos(1) + sin(1) + O(x**2)
    assert sin(pi*(1-x))._eval_nseries(x,2) == pi*x + O(x**2)
    raises(PoleError, 'sin(1/x)._eval_nseries(x,2)')

def test_doit():
    n = Symbol('n', integer = True)
    f = Sum(2 * n * x, (n, 1, 3))
    d = Derivative(f, x)
    assert d.doit() == 12
    assert d.doit(deep = False) == d
