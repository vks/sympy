"""Core module. Provides the basic operations needed in sympy.
"""

from sympify import sympify
from cache import cacheit
from basic import Basic, Atom, C
from singleton import S
from expr import Expr, AtomicExpr
from symbol import Symbol, Wild, symbols, var
from numbers import Number, Real, Rational, Integer, NumberSymbol,\
        RealNumber, igcd, ilcm, seterr
from power import Pow, integer_nthroot
from mul import Mul
from add import Add
from relational import Rel, Eq, Ne, Lt, Le, Gt, Ge, \
    Equality, Inequality, Unequality, StrictInequality
from multidimensional import vectorize
from function import Lambda, WildFunction, Derivative, diff, FunctionClass, \
    Function, expand, PoleError, expand_mul, expand_log, expand_func,\
    expand_trig, expand_complex
from sets import Set, Interval, Union, EmptySet
from evalf import PrecisionExhausted, N

# expose singletons like oo, I, etc.
Catalan = S.Catalan
E = S.Exp1
EulerGamma = S.EulerGamma
GoldenRatio = S.GoldenRatio
I = S.ImaginaryUnit
nan = S.NaN
oo = S.Infinity
pi= S.Pi
zoo = S.ComplexInfinity

