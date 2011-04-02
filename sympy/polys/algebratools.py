"""Classes defining properties of ground domains, e.g. ZZ, QQ, ZZ[x] ... """

from sympy.core import S, Basic, sympify

from sympy.polys.polyerrors import (
    ExactQuotientFailed,
    IsomorphismFailed,
    UnificationFailed,
    GeneratorsNeeded,
    CoercionFailed,
    NotInvertible,
    NotAlgebraic,
    DomainError,
)

import math

def factorial(m):
    """Returns `m!`. """
    if not m:
        return 1

    k = m

    while m > 1:
        m -= 1
        k *= m

    return k

class Algebra(object):
    """Represents an abstract domain. """

    dtype = None
    zero  = None
    one   = None

    has_Ring  = False
    has_Field = False

    has_assoc_Ring  = False
    has_assoc_Field = False

    is_ZZ = False
    is_QQ = False

    is_FF = False
    is_CC = False

    is_Poly = False
    is_Frac = False

    is_Exact = True

    is_Numerical = False
    is_Algebraic = False
    is_Composite = False

    has_CharacteristicZero = False

    is_EX = False

    rep = None

    def __init__(self):
        raise NotImplementedError

    def __str__(self):
        return self.rep

    def __repr__(self):
        return str(self)

    def __hash__(self):
        return hash((self.__class__.__name__, self.dtype))

    def __call__(self, *args):
        """Construct an element of `self` domain from `args`. """
        return self.dtype(*args)

    def normal(self, *args):
        return self.dtype(*args)

    def convert(K1, a, K0=None):
        """Convert an object `a` from `K0` to `K1`. """
        if K0 is not None:
            _convert = getattr(K1, "from_" + K0.__class__.__name__)

            if _convert is not None:
                result = _convert(a, K0)

                if result is not None:
                    return result

            raise CoercionFailed("can't convert %s of type %s to %s" % (a, K0, K1))
        else:
            try:
                if K1.of_type(a):
                    return a

                if type(a) is int:
                    return K1(a)

                if type(a) is long:
                    return K1(a)

                a = sympify(a)

                if isinstance(a, Basic):
                    return K1.from_sympy(a)
            except (TypeError, ValueError):
                pass

            raise CoercionFailed("can't convert %s to type %s" % (a, K1))

    def of_type(self, a):
        """Check if `a` is of type `dtype`. """
        return type(a) is type(self.one)

    def __contains__(self, a):
        """Check if `a` belongs to this domain. """
        try:
            self.convert(a)
        except CoercionFailed:
            return False

        return True

    def to_sympy(self, a):
        """Convert `a` to a SymPy object. """
        raise NotImplementedError

    def from_sympy(self, a):
        """Convert a SymPy object to `dtype`. """
        raise NotImplementedError

    def from_ZZ_python(K1, a, K0):
        """Convert a Python `int` object to `dtype`. """
        return None

    def from_QQ_python(K1, a, K0):
        """Convert a Python `Fraction` object to `dtype`. """
        return None

    def from_ZZ_sympy(K1, a, K0):
        """Convert a SymPy `Integer` object to `dtype`. """
        return None

    def from_QQ_sympy(K1, a, K0):
        """Convert a SymPy `Rational` object to `dtype`. """
        return None

    def from_ZZ_gmpy(K1, a, K0):
        """Convert a GMPY `mpz` object to `dtype`. """
        return None

    def from_QQ_gmpy(K1, a, K0):
        """Convert a GMPY `mpq` object to `dtype`. """
        return None

    def from_RR_sympy(K1, a, K0):
        """Convert a SymPy `Real` object to `dtype`. """
        return None

    def from_RR_mpmath(K1, a, K0):
        """Convert a mpmath `mpf` object to `dtype`. """
        return None

    def from_AlgebraicField(K1, a, K0):
        """Convert a `ANP` object to `dtype`. """
        return None

    def from_PolynomialRing(K1, a, K0):
        """Convert a `DMP` object to `dtype`. """
        if a.degree() <= 0:
            return K1.convert(a.LC(), K0.dom)

    def from_FractionField(K1, a, K0):
        """Convert a `DMF` object to `dtype`. """
        return None

    def from_ExpressionDomain(K1, a, K0):
        """Convert a `EX` object to `dtype`. """
        return K1.from_sympy(a.ex)

    def unify(K0, K1, gens=None):
        """Returns a maximal domain containg `K0` and `K1`. """
        if gens is not None:
            if (K0.is_Composite and (set(K0.gens) & set(gens))) or (K1.is_Composite and (set(K1.gens) & set(gens))):
                raise UnificationFailed("can't unify %s with %s, given %s generators" % (K0, K1, tuple(gens)))
        elif K0 == K1:
            return K0

        if K0.is_EX:
            return K0
        if K1.is_EX:
            return K1

        if not K0.is_Exact:
            return K0
        if not K1.is_Exact:
            return K1

        if K0.is_Composite:
            if K1.is_Composite:
                if K0.gens == K1.gens:
                    if K0.has_Field and K1.has_Field:
                        if K0.dom.has_Field:
                            return K0
                        else:
                            return K1
                    elif K0.has_Field:
                        if K0.dom == K1.dom:
                            return K0
                    elif K1.has_Field:
                        if K0.dom == K1.dom:
                            return K1
                    else:
                        if K0.dom.has_Field:
                            return K0
                        else:
                            return K1
                else:
                    gens = set(K0.gens + K1.gens)

                    try:
                        gens = sorted(gens)
                    except TypeError:
                        gens = list(gens)

                    if K0.has_Field and K1.has_Field:
                        if K0.dom.has_Field:
                            return K0.__class__(K0.dom, *gens)
                        else:
                            return K1.__class__(K1.dom, *gens)
                    elif K0.has_Field:
                        if K0.dom == K1.dom:
                            return K0.__class__(K0.dom, *gens)
                    elif K1.has_Field:
                        if K0.dom == K1.dom:
                            return K1.__class__(K1.dom, *gens)
                    else:
                        if K0.dom.has_Field:
                            return K0.__class__(K0.dom, *gens)
                        else:
                            return K1.__class__(K1.dom, *gens)
            elif K1.is_Algebraic:
                raise UnificationFailed("can't unify %s with %s" % (K0, K1))
            else:
                if K0.has_Field:
                    if K0.dom == K1:
                        return K0
                else:
                    if K0.dom.has_Field:
                        return K0
                    else:
                        return K0.__class__(K1, *K0.gens)
        elif K0.is_Algebraic:
            if K1.is_Composite:
                raise UnificationFailed("can't unify %s with %s" % (K0, K1))
            elif K1.is_Algebraic:
                raise NotImplementedError("unification of different algebraic extensions")
            elif K1.is_ZZ or K1.is_QQ:
                return K0
            else:
                raise UnificationFailed("can't unify %s with %s" % (K0, K1))
        else:
            if K1.is_Composite:
                if K1.has_Field:
                    if K0 == K1.dom:
                        return K1
                else:
                    if K1.dom.has_Field:
                        return K1
                    else:
                        return K1.__class__(K0, *K1.gens)
            elif K1.is_Algebraic:
                if K0.is_ZZ or K0.is_QQ:
                    return K1
                else:
                    raise UnificationFailed("can't unify %s with %s" % (K0, K1))
            else:
                if K0.has_Field:
                    return K0
                else:
                    return K1

        return ExpressionDomain()

    def __eq__(self, other):
        """Returns `True` if two algebras are equivalent. """
        return self.dtype == other.dtype

    def __ne__(self, other):
        """Returns `False` if two algebras are equivalent. """
        return self.dtype != other.dtype

    def get_ring(self):
        """Returns a ring associated with `self`. """
        raise DomainError('there is no ring associated with %s' % self)

    def get_field(self):
        """Returns a field associated with `self`. """
        raise DomainError('there is no field associated with %s' % self)

    def get_exact(self):
        """Returns an exact domain associated with `self`. """
        return self

    def float_domain(self):
        return FF

    def complex_domain(self):
        return CC

    def __getitem__(self, gens):
        """The mathematical way do make a polynomial ring. """
        if hasattr(gens, '__iter__'):
            return self.poly_ring(*gens)
        else:
            return self.poly_ring(gens)

    def poly_ring(self, *gens):
        """Returns a polynomial ring, i.e. `K[X]`. """
        return PolynomialRing(self, *gens)

    def frac_field(self, *gens):
        """Returns a fraction field, i.e. `K(X)`. """
        return FractionField(self, *gens)

    def algebraic_field(self, *extension):
        """Returns an algebraic field, i.e. `K(alpha, ...)`. """
        raise DomainError("can't create algebraic field over %s" % self)

    def is_zero(self, a):
        """Returns True if `a` is zero. """
        return not a

    def is_one(self, a):
        """Returns True if `a` is one. """
        return a == self.one

    def is_positive(self, a):
        """Returns True if `a` is positive. """
        return a > 0

    def is_negative(self, a):
        """Returns True if `a` is negative. """
        return a < 0

    def is_nonpositive(self, a):
        """Returns True if `a` is non-positive. """
        return a <= 0

    def is_nonnegative(self, a):
        """Returns True if `a` is non-negative. """
        return a >= 0

    def abs(self, a):
        """Absolute value of `a`, implies `__abs__`. """
        return abs(a)

    def neg(self, a):
        """Returns `a` negated, implies `__neg__`. """
        return -a

    def pos(self, a):
        """Returns `a` positive, implies `__pos__`. """
        return +a

    def add(self, a, b):
        """Sum of `a` and `b`, implies `__add__`.  """
        return a + b

    def sub(self, a, b):
        """Difference of `a` and `b`, implies `__sub__`.  """
        return a - b

    def mul(self, a, b):
        """Product of `a` and `b`, implies `__mul__`.  """
        return a * b

    def pow(self, a, b):
        """Raise `a` to power `b`, implies `__pow__`.  """
        return a ** b

    def exquo(self, a, b):
        """Exact quotient of `a` and `b`, implies something. """
        raise NotImplementedError

    def quo(self, a, b):
        """Quotient of `a` and `b`, implies something.  """
        raise NotImplementedError

    def rem(self, a, b):
        """Remainder of `a` and `b`, implies `__mod__`.  """
        raise NotImplementedError

    def div(self, a, b):
        """Division of `a` and `b`, implies something. """
        raise NotImplementedError

    def invert(self, a, b):
        """Returns inversion of `a mod b`, implies something. """
        raise NotImplementedError

    def numer(self, a):
        """Returns numerator of `a`. """
        raise NotImplementedError

    def denom(self, a):
        """Returns denominator of `a`. """
        raise NotImplementedError

    def gcdex(self, a, b):
        """Extended GCD of `a` and `b`. """
        raise NotImplementedError

    def gcd(self, a, b):
        """Returns GCD of `a` and `b`. """
        raise NotImplementedError

    def lcm(self, a, b):
        """Returns LCM of `a` and `b`. """
        raise NotImplementedError

    def log(self, a, b):
        """Returns b-base logarithm of `a`. """
        raise NotImplementedError

    def sqrt(self, a):
        """Returns square root of `a`. """
        raise NotImplementedError

    def factorial(self, a):
        """Returns factorial of `a`. """
        return self.dtype(factorial(a))

    def evalf(self, a, **args):
        """Returns numerical approximation of `a`. """
        return self.to_sympy(a).evalf(**args)

    def real(self, a):
        return a

    def imag(self, a):
        return self.zero

class Ring(Algebra):
    """Represents a ring domain. """

    has_Ring = True

    def get_ring(self):
        """Returns a ring associated with `self`. """
        return self

    def exquo(self, a, b):
        """Exact quotient of `a` and `b`, implies `__floordiv__`.  """
        return a // b

    def quo(self, a, b):
        """Quotient of `a` and `b`, implies `__floordiv__`. """
        if a % b:
            raise ExactQuotientFailed('%s does not divide %s in %s' % (b, a, self))
        else:
            return a // b

    def rem(self, a, b):
        """Remainder of `a` and `b`, implies `__mod__`.  """
        return a % b

    def div(self, a, b):
        """Division of `a` and `b`, implies `__divmod__`. """
        return divmod(a, b)

    def invert(self, a, b):
        """Returns inversion of `a mod b`. """
        s, t, h = self.gcdex(a, b)

        if self.is_one(h):
            return s % b
        else:
            raise NotInvertible("zero divisor")

    def numer(self, a):
        """Returns numerator of `a`. """
        return a

    def denom(self, a):
        """Returns denominator of `a`. """
        return self.one

class Field(Ring):
    """Represents a field domain. """

    has_Field = True

    def get_field(self):
        """Returns a field associated with `self`. """
        return self

    def exquo(self, a, b):
        """Exact quotient of `a` and `b`, implies `__div__`.  """
        return a / b

    def quo(self, a, b):
        """Quotient of `a` and `b`, implies `__div__`. """
        return a / b

    def rem(self, a, b):
        """Remainder of `a` and `b`, implies nothing.  """
        return self.zero

    def div(self, a, b):
        """Division of `a` and `b`, implies `__div__`. """
        return a / b, self.zero

    def gcd(self, a, b):
        """Returns GCD of `a` and `b`. """
        return self.one

    def lcm(self, a, b):
        """Returns LCM of `a` and `b`. """
        return a*b

class IntegerRing(Ring):
    """General class for integer rings. """

    is_ZZ = True
    rep   = 'ZZ'

    is_Numerical = True

    has_assoc_Ring         = True
    has_assoc_Field        = True

    has_CharacteristicZero = True

    def get_field(self):
        """Returns a field associated with `self`. """
        return QQ

    def from_AlgebraicField(K1, a, K0):
        """Convert a `ANP` object to `dtype`. """
        if a.is_ground:
            return K1.convert(a.LC(), K0.dom)

    def log(self, a, b):
        """Returns b-base logarithm of `a`. """
        return self.dtype(math.log(a, b))

class RationalField(Field):
    """General class for rational fields. """

    is_QQ = True
    rep   = 'QQ'

    is_Numerical = True

    has_assoc_Ring         = True
    has_assoc_Field        = True

    has_CharacteristicZero = True

    def get_ring(self):
        """Returns a ring associated with `self`. """
        return ZZ

    def algebraic_field(self, *extension):
        """Returns an algebraic field, i.e. `QQ(alpha, ...)`. """
        return AlgebraicField(self, *extension)

    def from_AlgebraicField(K1, a, K0):
        """Convert a `ANP` object to `dtype`. """
        if a.is_ground:
            return K1.convert(a.LC(), K0.dom)

class ZZ_python(IntegerRing):
    pass
class QQ_python(RationalField):
    pass
class ZZ_sympy(IntegerRing):
    pass
class QQ_sympy(RationalField):
    pass
class ZZ_gmpy(IntegerRing):
    pass
class QQ_gmpy(RationalField):
    pass

class PolynomialRing(Ring):
    pass
class FractionField(Field):
    pass

class ExpressionDomain(Field):
    pass

HAS_FRACTION = True

try:
    import fractions
except ImportError:
    HAS_FRACTION = False

HAS_GMPY = True

try:
    import gmpy
except ImportError:
    HAS_GMPY = False

from sympy.core.numbers import (
    igcdex as python_gcdex,
    igcd as python_gcd,
    ilcm as python_lcm,
)

from sympy.mpmath.libmp.libmpf import (
    isqrt as python_sqrt,
)

from __builtin__ import (
    int as python_int,
)

if HAS_FRACTION:
    from fractions import (
        Fraction as python_rat,
    )

class ZZ_python(IntegerRing):
    """Integer ring based on Python int class. """

    dtype = python_int
    zero  = dtype(0)
    one   = dtype(1)

    def __init__(self):
        pass

    def to_sympy(self, a):
        """Convert `a` to a SymPy object. """
        return sympy_int(a)

    def from_sympy(self, a):
        """Convert SymPy's Integer to `dtype`. """
        if a.is_Integer:
            return python_int(a.p)
        elif a.is_Real and int(a) == a:
            return sympy_int(int(a))
        else:
            raise CoercionFailed("expected `Integer` object, got %s" % a)

    def from_ZZ_python(K1, a, K0):
        """Convert a Python `int` object to `dtype`. """
        return a

    def from_QQ_python(K1, a, K0):
        """Convert a Python `Fraction` object to `dtype`. """
        if a.denominator == 1:
            return a.numerator

    def from_ZZ_sympy(K1, a, K0):
        """Convert a SymPy `Integer` object to `dtype`. """
        return a.p

    def from_QQ_sympy(K1, a, K0):
        """Convert a SymPy `Rational` object to `dtype`. """
        if a.q == 1:
            return a.p

    def from_ZZ_gmpy(K1, a, K0):
        """Convert a GMPY `mpz` object to `dtype`. """
        return python_int(a)

    def from_QQ_gmpy(K1, a, K0):
        """Convert a GMPY `mpq` object to `dtype`. """
        if a.denom() == 1:
            return python_int(a.numer())

    def from_RR_sympy(K1, a, K0):
        """Convert a SymPy `Real` object to `dtype`. """
        p, q = K0.as_integer_ratio(a)

        if q == 1:
            return python_int(p)

    def from_RR_mpmath(K1, a, K0):
        """Convert a mpmath `mpf` object to `dtype`. """
        p, q = K0.as_integer_ratio(a)

        if q == 1:
            return python_int(p)

    def gcdex(self, a, b):
        """Extended GCD of `a` and `b`. """
        return python_gcdex(a, b)

    def gcd(self, a, b):
        """Returns GCD of `a` and `b`. """
        return python_gcd(a, b)

    def lcm(self, a, b):
        """Returns LCM of `a` and `b`. """
        return python_lcm(a, b)

    def sqrt(self, a):
        """Returns square root of `a`. """
        return python_int(python_sqrt(a))

if HAS_FRACTION:
    class QQ_python(RationalField):
        """Rational field based on Python Fraction class. """

        dtype = python_rat
        zero  = dtype(0)
        one   = dtype(1)

        def __init__(self):
            pass

        def to_sympy(self, a):
            """Convert `a` to a SymPy object. """
            return sympy_rat(a.numerator, a.denominator)

        def from_sympy(self, a):
            """Convert SymPy's Rational to `dtype`. """
            if a.is_Rational and a.q != 0:
                return python_rat(a.p, a.q)
            elif a.is_Real:
                return python_rat(*RR.as_integer_ratio(a))
            else:
                raise CoercionFailed("expected `Rational` object, got %s" % a)

        def from_ZZ_python(K1, a, K0):
            """Convert a Python `int` object to `dtype`. """
            return python_rat(a)

        def from_QQ_python(K1, a, K0):
            """Convert a Python `Fraction` object to `dtype`. """
            return a

        def from_ZZ_sympy(K1, a, K0):
            """Convert a SymPy `Integer` object to `dtype`. """
            return python_rat(a.p)

        def from_QQ_sympy(K1, a, K0):
            """Convert a SymPy `Rational` object to `dtype`. """
            return python_rat(a.p, a.q)

        def from_ZZ_gmpy(K1, a, K0):
            """Convert a GMPY `mpz` object to `dtype`. """
            return python_rat(python_int(a))

        def from_QQ_gmpy(K1, a, K0):
            """Convert a GMPY `mpq` object to `dtype`. """
            return python_rat(python_int(a.numer()),
                              python_int(a.denom()))

        def from_RR_sympy(K1, a, K0):
            """Convert a SymPy `Real` object to `dtype`. """
            return python_rat(*K0.as_integer_ratio(a))

        def from_RR_mpmath(K1, a, K0):
            """Convert a mpmath `mpf` object to `dtype`. """
            return python_rat(*K0.as_integer_ratio(a))

        def numer(self, a):
            """Returns numerator of `a`. """
            return a.numerator

        def denom(self, a):
            """Returns denominator of `a`. """
            return a.denominator

from sympy import (
    Integer as sympy_int,
    Rational as sympy_rat,
)

from sympy.core.numbers import (
    igcdex as sympy_gcdex,
    igcd as sympy_gcd,
    ilcm as sympy_lcm,
)

from sympy.mpmath.libmp.libmpf import (
    isqrt as sympy_sqrt,
)

class ZZ_sympy(IntegerRing):
    """Integer ring based on SymPy Integer class. """

    dtype = sympy_int
    zero  = dtype(0)
    one   = dtype(1)

    def __init__(self):
        pass

    def to_sympy(self, a):
        """Convert `a` to a SymPy object. """
        return a

    def from_sympy(self, a):
        """Convert SymPy's Integer to `dtype`. """
        if a.is_Integer:
            return a
        elif a.is_Real and int(a) == a:
            return sympy_int(int(a))
        else:
            raise CoercionFailed("expected Integer object, got %s" % a)

    def from_ZZ_python(K1, a, K0):
        """Convert a Python `int` object to `dtype`. """
        return sympy_int(a)

    def from_QQ_python(K1, a, K0):
        """Convert a Python `Fraction` object to `dtype`. """
        if a.denominator == 1:
            return sympy_int(a.numerator)

    def from_ZZ_sympy(K1, a, K0):
        """Convert a SymPy `Integer` object to `dtype`. """
        return a

    def from_QQ_sympy(K1, a, K0):
        """Convert a SymPy `Rational` object to `dtype`. """
        if a.q == 1:
            return sympy_int(a.p)

    def from_ZZ_gmpy(K1, a, K0):
        """Convert a GMPY `mpz` object to `dtype`. """
        return sympy_int(python_int(a))

    def from_QQ_gmpy(K1, a, K0):
        """Convert a GMPY `mpq` object to `dtype`. """
        if a.denom() == 1:
            return sympy_int(python_int(a.numer()))

    def from_RR_sympy(K1, a, K0):
        """Convert a SymPy `Real` object to `dtype`. """
        p, q = K0.as_integer_ratio(a)

        if q == 1:
            return sympy_int(p)

    def from_RR_mpmath(K1, a, K0):
        """Convert a mpmath `mpf` object to `dtype`. """
        p, q = K0.as_integer_ratio(a)

        if q == 1:
            return sympy_int(p)

    def gcdex(self, a, b):
        """Extended GCD of `a` and `b`. """
        return map(sympy_int, sympy_gcdex(int(a), int(b)))

    def gcd(self, a, b):
        """Returns GCD of `a` and `b`. """
        return sympy_int(sympy_gcd(int(a), int(b)))

    def lcm(self, a, b):
        """Returns LCM of `a` and `b`. """
        return sympy_int(sympy_lcm(int(a), int(b)))

    def sqrt(self, a):
        """Returns square root of `a`. """
        return sympy_int(int(sympy_sqrt(int(a))))

class QQ_sympy(RationalField):
    """Rational field based on SymPy Rational class. """

    dtype = sympy_rat
    zero  = dtype(0)
    one   = dtype(1)

    def __init__(self):
        pass

    def to_sympy(self, a):
        """Convert `a` to a SymPy object. """
        return a

    def from_sympy(self, a):
        """Convert SymPy's Rational to `dtype`. """
        if a.is_Rational and a.q != 0:
            return a
        elif a.is_Real:
            return sympy_rat(*RR.as_integer_ratio(a))
        else:
            raise CoercionFailed("expected `Rational` object, got %s" % a)

    def from_ZZ_python(K1, a, K0):
        """Convert a Python `int` object to `dtype`. """
        return sympy_rat(a)

    def from_QQ_python(K1, a, K0):
        """Convert a Python `Fraction` object to `dtype`. """
        return sympy_rat(a.numerator, a.denominator)

    def from_ZZ_sympy(K1, a, K0):
        """Convert a SymPy `Integer` object to `dtype`. """
        return sympy_rat(a.p)

    def from_QQ_sympy(K1, a, K0):
        """Convert a SymPy `Rational` object to `dtype`. """
        return a

    def from_ZZ_gmpy(K1, a, K0):
        """Convert a GMPY `mpz` object to `dtype`. """
        return sympy_rat(python_int(a))

    def from_QQ_gmpy(K1, a, K0):
        """Convert a GMPY `mpq` object to `dtype`. """
        return sympy_rat(python_int(a.numer()),
                         python_int(a.denom()))

    def from_RR_sympy(K1, a, K0):
        """Convert a SymPy `Real` object to `dtype`. """
        return sympy_rat(*K0.as_integer_ratio(a))

    def from_RR_mpmath(K1, a, K0):
        """Convert a mpmath `mpf` object to `dtype`. """
        return sympy_rat(*K0.as_integer_ratio(a))

    def numer(self, a):
        """Returns numerator of `a`. """
        return sympy_int(a.p)

    def denom(self, a):
        """Returns denominator of `a`. """
        return sympy_int(a.q)

if HAS_GMPY:
    from gmpy import (
        mpz as gmpy_int,
        mpq as gmpy_rat,
        numer as gmpy_numer,
        denom as gmpy_denom,
        gcdext as gmpy_gcdex,
        gcd as gmpy_gcd,
        lcm as gmpy_lcm,
        sqrt as gmpy_sqrt,
        fac as gmpy_factorial,
    )

    class ZZ_gmpy(IntegerRing):
        """Integer ring based on GMPY mpz class. """

        dtype = gmpy_int
        zero  = dtype(0)
        one   = dtype(1)

        def __init__(self):
            pass

        def to_sympy(self, a):
            """Convert `a` to a SymPy object. """
            return sympy_int(int(a))

        def from_sympy(self, a):
            """Convert SymPy's Integer to `dtype`. """
            if a.is_Integer:
                return gmpy_int(a.p)
            elif a.is_Real and int(a) == a:
                return gmpy_int(int(a))
            else:
                raise CoercionFailed("expected Integer object, got %s" % a)

        def from_ZZ_python(K1, a, K0):
            """Convert a Python `int` object to `dtype`. """
            return gmpy_int(a)

        def from_QQ_python(K1, a, K0):
            """Convert a Python `Fraction` object to `dtype`. """
            if a.denominator == 1:
                return gmpy_int(a.numerator)

        def from_ZZ_sympy(K1, a, K0):
            """Convert a SymPy `Integer` object to `dtype`. """
            return gmpy_int(a.p)

        def from_QQ_sympy(K1, a, K0):
            """Convert a SymPy `Rational` object to `dtype`. """
            if a.q == 1:
                return gmpy_int(a.p)

        def from_ZZ_gmpy(K1, a, K0):
            """Convert a GMPY `mpz` object to `dtype`. """
            return a

        def from_QQ_gmpy(K1, a, K0):
            """Convert a GMPY `mpq` object to `dtype`. """
            if a.denom() == 1:
                return a.numer()

        def from_RR_sympy(K1, a, K0):
            """Convert a SymPy `Real` object to `dtype`. """
            p, q = K0.as_integer_ratio(a)

            if q == 1:
                return gmpy_int(p)

        def from_RR_mpmath(K1, a, K0):
            """Convert a mpmath `mpf` object to `dtype`. """
            p, q = K0.as_integer_ratio(a)

            if q == 1:
                return gmpy_int(p)

        def gcdex(self, a, b):
            """Extended GCD of `a` and `b`. """
            h, s, t = gmpy_gcdex(a, b)
            return s, t, h

        def gcd(self, a, b):
            """Returns GCD of `a` and `b`. """
            return gmpy_gcd(a, b)

        def lcm(self, a, b):
            """Returns LCM of `a` and `b`. """
            return gmpy_lcm(a, b)

        def sqrt(self, a):
            """Returns square root of `a`. """
            return gmpy_sqrt(a)

        def factorial(self, a):
            """Returns factorial of `a`. """
            return gmpy_factorial(int(a))

    class QQ_gmpy(RationalField):
        """Rational field based on GMPY mpq class. """

        dtype = gmpy_rat
        zero  = dtype(0)
        one   = dtype(1)

        def __init__(self):
            pass

        def to_sympy(self, a):
            """Convert `a` to a SymPy object. """
            return sympy_rat(int(gmpy_numer(a)),
                             int(gmpy_denom(a)))

        def from_sympy(self, a):
            """Convert SymPy's Integer to `dtype`. """
            if a.is_Rational and a.q != 0:
                return gmpy_rat(a.p, a.q)
            elif a.is_Real:
                return gmpy_rat(*RR.as_integer_ratio(a))
            else:
                raise CoercionFailed("expected `Rational` object, got %s" % a)

        def from_ZZ_python(K1, a, K0):
            """Convert a Python `int` object to `dtype`. """
            return gmpy_rat(a)

        def from_QQ_python(K1, a, K0):
            """Convert a Python `Fraction` object to `dtype`. """
            return gmpy_rat(a.numerator, a.denominator)

        def from_ZZ_sympy(K1, a, K0):
            """Convert a SymPy `Integer` object to `dtype`. """
            return gmpy_rat(a.p)

        def from_QQ_sympy(K1, a, K0):
            """Convert a SymPy `Rational` object to `dtype`. """
            return gmpy_rat(a.p, a.q)

        def from_ZZ_gmpy(K1, a, K0):
            """Convert a GMPY `mpz` object to `dtype`. """
            return gmpy_rat(a)

        def from_QQ_gmpy(K1, a, K0):
            """Convert a GMPY `mpq` object to `dtype`. """
            return a

        def from_RR_sympy(K1, a, K0):
            """Convert a SymPy `Real` object to `dtype`. """
            return gmpy_rat(*K0.as_integer_ratio(a))

        def from_RR_mpmath(K1, a, K0):
            """Convert a mpmath `mpf` object to `dtype`. """
            return gmpy_rat(*K0.as_integer_ratio(a))

        def exquo(self, a, b):
            """Exact quotient of `a` and `b`, implies `__div__`.  """
            return gmpy_rat(a.qdiv(b))

        def quo(self, a, b):
            """Quotient of `a` and `b`, implies `__div__`. """
            return gmpy_rat(a.qdiv(b))

        def rem(self, a, b):
            """Remainder of `a` and `b`, implies nothing.  """
            return self.zero

        def div(self, a, b):
            """Division of `a` and `b`, implies `__div__`. """
            return gmpy_rat(a.qdiv(b)), self.zero

        def numer(self, a):
            """Returns numerator of `a`. """
            return gmpy_numer(a)

        def denom(self, a):
            """Returns denominator of `a`. """
            return gmpy_denom(a)

        def factorial(self, a):
            """Returns factorial of `a`. """
            return gmpy_rat(gmpy_factorial(int(a)))

class RealAlgebra(Algebra):
    """Abstract algebra for real numbers. """

    rep   = 'RR'

    is_Exact     = False
    is_Numerical = True

    has_CharacteristicZero = True

    def as_integer_ratio(self, a, **args):
        """Convert real number to a (numer, denom) pair. """
        v, n = math.frexp(a) # XXX: hack, will work only for floats

        for i in xrange(300):
            if v != math.floor(v):
                v, n = 2*v, n-1
            else:
                break

        numer, denom = int(v), 1

        m = 1 << abs(n)

        if n > 0:
            numer *= m
        else:
            denom = m

        return self.limit_denom(numer, denom, **args)

    def limit_denom(self, n, d, **args):
        """Find closest rational to `n/d` (up to `max_denom`). """
        max_denom = args.get('max_denom', 1000000)

        if d <= max_denom:
            return n, d

        self = QQ(n, d)

        p0, q0, p1, q1 = 0, 1, 1, 0

        while True:
            a  = n//d
            q2 = q0 + a*q1

            if q2 > max_denom:
                break

            p0, q0, p1, q1, n, d = \
                p1, q1, p0 + a*p1, q2, d, n - a*d

        k = (max_denom - q0)//q1

        P1, Q1 = p0 + k*p1, q0 + k*q1

        bound1 = QQ(P1, Q1)
        bound2 = QQ(p1, q1)

        if abs(bound2 - self) <= abs(bound1 - self):
            return p1, q1
        else:
            return P1, Q1

    def get_ring(self):
        """Returns a ring associated with `self`. """
        raise DomainError('there is no ring associated with %s' % self)

    def get_field(self):
        """Returns a field associated with `self`. """
        raise DomainError('there is no field associated with %s' % self)

    def get_exact(self):
        """Returns an exact domain associated with `self`. """
        return QQ

    def exquo(self, a, b):
        """Exact quotient of `a` and `b`, implies `__div__`.  """
        return a / b

    def quo(self, a, b):
        """Quotient of `a` and `b`, implies `__div__`. """
        return a / b

    def rem(self, a, b):
        """Remainder of `a` and `b`, implies nothing.  """
        return self.zero

    def div(self, a, b):
        """Division of `a` and `b`, implies `__div__`. """
        return a / b, self.zero

from sympy import (
    Real as sympy_mpf,
)

class RR_sympy(RealAlgebra):
    """Algebra for real numbers based on SymPy Real type. """

    dtype = sympy_mpf
    zero  = dtype(0)
    one   = dtype(1)

    def __init__(self):
        pass

    def to_sympy(self, a):
        """Convert `a` to a SymPy object. """
        return a

    def from_sympy(self, a):
        """Convert SymPy's Integer to `dtype`. """
        b = a.evalf()

        if b.is_Real and b not in [S.Infinity, S.NegativeInfinity]:
            return b
        else:
            raise CoercionFailed("expected Real object, got %s" % a)

    def from_ZZ_python(K1, a, K0):
        """Convert a Python `int` object to `dtype`. """
        return sympy_mpf(a)

    def from_QQ_python(K1, a, K0):
        """Convert a Python `Fraction` object to `dtype`. """
        return sympy_mpf(a.numerator) / a.denominator

    def from_ZZ_sympy(K1, a, K0):
        """Convert a SymPy `Integer` object to `dtype`. """
        return sympy_mpf(a.p)

    def from_QQ_sympy(K1, a, K0):
        """Convert a SymPy `Rational` object to `dtype`. """
        return sympy_mpf(a.p) / a.q

    def from_ZZ_gmpy(K1, a, K0):
        """Convert a GMPY `mpz` object to `dtype`. """
        return sympy_mpf(int(a))

    def from_QQ_gmpy(K1, a, K0):
        """Convert a GMPY `mpq` object to `dtype`. """
        return sympy_mpf(int(a.numer())) / int(a.denom())

    def from_RR_sympy(K1, a, K0):
        """Convert a SymPy `Real` object to `dtype`. """
        return a

    def from_RR_mpmath(K1, a, K0):
        """Convert a mpmath `mpf` object to `dtype`. """
        return sympy_mpf(a)

from sympy.mpmath import (
    mpf as mpmath_mpf,
)

class RR_mpmath(RealAlgebra):
    """Algebra for real numbers based on mpmath mpf type. """

    dtype = mpmath_mpf
    zero  = dtype(0)
    one   = dtype(1)

    def __init__(self):
        pass

    def to_sympy(self, a):
        """Convert `a` to a SymPy object. """
        return sympy_mpf(a)

    def from_sympy(self, a):
        """Convert SymPy's Integer to `dtype`. """
        b = a.evalf()

        if b.is_Real and b not in [S.Infinity, S.NegativeInfinity]:
            return mpmath_mpf(b)
        else:
            raise CoercionFailed("expected Real object, got %s" % a)

    def from_ZZ_python(K1, a, K0):
        """Convert a Python `int` object to `dtype`. """
        return mpmath_mpf(a)

    def from_QQ_python(K1, a, K0):
        """Convert a Python `Fraction` object to `dtype`. """
        return mpmath_mpf(a.numerator) / a.denominator

    def from_ZZ_sympy(K1, a, K0):
        """Convert a SymPy `Integer` object to `dtype`. """
        return mpmath_mpf(a.p)

    def from_QQ_sympy(K1, a, K0):
        """Convert a SymPy `Rational` object to `dtype`. """
        return mpmath_mpf(a.p) / a.q

    def from_ZZ_gmpy(K1, a, K0):
        """Convert a GMPY `mpz` object to `dtype`. """
        return mpmath_mpf(int(a))

    def from_QQ_gmpy(K1, a, K0):
        """Convert a GMPY `mpq` object to `dtype`. """
        return mpmath_mpf(int(a.numer())) / int(a.denom())

    def from_RR_sympy(K1, a, K0):
        """Convert a SymPy `Real` object to `dtype`. """
        return mpmath_mpf(a)

    def from_RR_mpmath(K1, a, K0):
        """Convert a mpmath `mpf` object to `dtype`. """
        return a

class FF_float(RealAlgebra): # XXX: tmp solution
    """Float domain. """

    rep   = 'FF'

    is_FF = True

    dtype = float
    zero  = dtype(0)
    one   = dtype(1)

    def __init__(self):
        pass

    def normal(self, a):
        if abs(a) < 1e-15:
            return self.zero
        else:
            return self.dtype(a)

    def to_sympy(self, a):
        """Convert `a` to a SymPy object. """
        return sympy_mpf(a)

    def from_sympy(self, a):
        """Convert SymPy's Integer to `dtype`. """
        b = a.evalf()

        if b.is_Real and b not in [S.Infinity, S.NegativeInfinity]:
            return float(b)
        else:
            raise CoercionFailed("expected Real object, got %s" % a)

    def from_ZZ_python(K1, a, K0):
        """Convert a Python `int` object to `dtype`. """
        return K1.dtype(a)

    def from_QQ_python(K1, a, K0):
        """Convert a Python `Fraction` object to `dtype`. """
        return K1.dtype(a.numerator) / a.denominator

    def from_ZZ_sympy(K1, a, K0):
        """Convert a SymPy `Integer` object to `dtype`. """
        return K1.dtype(a.p)

    def from_QQ_sympy(K1, a, K0):
        """Convert a SymPy `Rational` object to `dtype`. """
        return K1.dtype(a.p) / a.q

    def from_ZZ_gmpy(K1, a, K0):
        """Convert a GMPY `mpz` object to `dtype`. """
        return K1.dtype(int(a))

    def from_QQ_gmpy(K1, a, K0):
        """Convert a GMPY `mpq` object to `dtype`. """
        return K1.dtype(int(a.numer())) / int(a.denom)

    def from_RR_sympy(K1, a, K0):
        """Convert a SymPy `Real` object to `dtype`. """
        return K1.dtype(a)

    def from_RR_mpmath(K1, a, K0):
        """Convert a mpmath `mpf` object to `dtype`. """
        return K1.dtype(a)

    def complex_domain(self):
        return CC

class CC_complex(RealAlgebra): # XXX: tmp solution
    """Complex domain. """

    rep   = 'CC'

    dtype = complex
    zero  = dtype(0)
    one   = dtype(1)

    def __init__(self):
        pass

    def to_sympy(self, a):
        """Convert `a` to a SymPy object. """
        return sympy_mpf(a)

    def from_sympy(self, a):
        """Convert SymPy's Integer to `dtype`. """
        b = a.evalf()

        if b.is_Real and b not in [S.Infinity, S.NegativeInfinity]:
            return float(b)
        else:
            raise CoercionFailed("expected Real object, got %s" % a)

    def from_ZZ_python(K1, a, K0):
        """Convert a Python `int` object to `dtype`. """
        return K1.dtype(a)

    def from_QQ_python(K1, a, K0):
        """Convert a Python `Fraction` object to `dtype`. """
        return K1.dtype(a.numerator) / a.denominator

    def from_ZZ_sympy(K1, a, K0):
        """Convert a SymPy `Integer` object to `dtype`. """
        return K1.dtype(a.p)

    def from_QQ_sympy(K1, a, K0):
        """Convert a SymPy `Rational` object to `dtype`. """
        return K1.dtype(a.p) / a.q

    def from_ZZ_gmpy(K1, a, K0):
        """Convert a GMPY `mpz` object to `dtype`. """
        return K1.dtype(int(a))

    def from_QQ_gmpy(K1, a, K0):
        """Convert a GMPY `mpq` object to `dtype`. """
        return K1.dtype(int(a.numer())) / int(a.denom)

    def from_RR_sympy(K1, a, K0):
        """Convert a SymPy `Real` object to `dtype`. """
        return K1.dtype(a)

    def from_RR_mpmath(K1, a, K0):
        """Convert a mpmath `mpf` object to `dtype`. """
        return K1.dtype(a)

    def from_FF_float(K1, a, K0):
        return K1.dtype(a)

    def real(self, a):
        return a.real

    def imag(self, a):
        return a.imag

FF = FF_float()
CC = CC_complex()

def _getenv(key, default=None):
    from os import getenv
    return getenv(key, default)

GROUND_TYPES = _getenv('SYMPY_GROUND_TYPES', 'gmpy').lower()

if GROUND_TYPES == 'python':  # XXX: needs 2.6 or better (at least for now)
    ZZ = ZZ_python()

    if HAS_FRACTION:
        QQ = QQ_python()
    elif HAS_GMPY:
        QQ = QQ_gmpy()
        GROUND_TYPES = 'python/gmpy'
    else:
        QQ = QQ_sympy()
        GROUND_TYPES = 'python/sympy'
elif GROUND_TYPES == 'sympy': # XXX: this is *very* slow, guess why ;)
    ZZ = ZZ_sympy()
    QQ = QQ_sympy()
elif GROUND_TYPES == 'gmpy':  # XXX: should be fine? sorry, but no, try -Qnew, damn
    if HAS_GMPY:
        ZZ = ZZ_gmpy()
        QQ = QQ_gmpy()
    else:
        ZZ = ZZ_python()

        if HAS_FRACTION:
            QQ = QQ_python()
            GROUND_TYPES = 'python'
        else:
            QQ = QQ_sympy()
            GROUND_TYPES = 'python/sympy'
else:
    raise ValueError("invalid ground types: %s" % GROUND_TYPES)

RR = RR_mpmath()

from sympy.polys.polyclasses import DMP, DMF, ANP

from sympy.polys.polyutils import (
    dict_from_basic,
    basic_from_dict,
    _dict_reorder,
)

class AlgebraicField(Field):
    """A class for representing algebraic number fields. """

    dtype        = ANP

    is_Numerical = True
    is_Algebraic = True

    has_assoc_Ring  = False
    has_assoc_Field = True

    has_CharacteristicZero = True

    def __init__(self, dom, *ext):
        if not dom.is_QQ:
            raise DomainError("ground domain must be a rational field")

        from sympy.polys.numberfields import to_number_field

        self.ext = to_number_field(ext)
        self.mod = self.ext.minpoly.rep

        self.dom  = dom

        self.gens = (self.ext,)
        self.unit = self([dom(1), dom(0)])

        self.zero = self.dtype.zero(self.mod.rep, dom)
        self.one  = self.dtype.one(self.mod.rep, dom)

    def __str__(self):
        return str(self.dom) + '<' + str(self.ext) + '>'

    def __hash__(self):
        return hash((self.__class__.__name__, self.dtype, self.dom, self.ext))

    def __call__(self, a):
        """Construct an element of `self` domain from `a`. """
        return ANP(a, self.mod.rep, self.dom)

    def __eq__(self, other):
        """Returns `True` if two algebras are equivalent. """
        if self.dtype == other.dtype:
            return self.ext == other.ext
        else:
            return False

    def __ne__(self, other):
        """Returns `False` if two algebras are equivalent. """
        if self.dtype == other.dtype:
            return self.ext != other.ext
        else:
            return True

    def to_sympy(self, a):
        """Convert `a` to a SymPy object. """
        from sympy.polys.numberfields import AlgebraicNumber
        return AlgebraicNumber(self.ext, a).as_basic()

    def from_sympy(self, a):
        """Convert SymPy's expression to `dtype`. """
        try:
            return self([self.dom.from_sympy(a)])
        except CoercionFailed:
            pass

        from sympy.polys.numberfields import to_number_field

        try:
            return self(to_number_field(a, self.ext).native_coeffs())
        except (NotAlgebraic, IsomorphismFailed):
            raise CoercionFailed("%s is not a valid algebraic number in %s" % (a, self))

    def from_ZZ_python(K1, a, K0):
        """Convert a Python `int` object to `dtype`. """
        return K1(K1.dom.convert(a, K0))

    def from_QQ_python(K1, a, K0):
        """Convert a Python `Fraction` object to `dtype`. """
        return K1(K1.dom.convert(a, K0))

    def from_ZZ_sympy(K1, a, K0):
        """Convert a SymPy `Integer` object to `dtype`. """
        return K1(K1.dom.convert(a, K0))

    def from_QQ_sympy(K1, a, K0):
        """Convert a SymPy `Rational` object to `dtype`. """
        return K1(K1.dom.convert(a, K0))

    def from_ZZ_gmpy(K1, a, K0):
        """Convert a GMPY `mpz` object to `dtype`. """
        return K1(K1.dom.convert(a, K0))

    def from_QQ_gmpy(K1, a, K0):
        """Convert a GMPY `mpq` object to `dtype`. """
        return K1(K1.dom.convert(a, K0))

    def from_RR_sympy(K1, a, K0):
        """Convert a SymPy `Real` object to `dtype`. """
        return K1(K1.dom.convert(a, K0))

    def from_RR_mpmath(K1, a, K0):
        """Convert a mpmath `mpf` object to `dtype`. """
        return K1(K1.dom.convert(a, K0))

    def get_ring(self):
        """Returns a ring associated with `self`. """
        raise DomainError('there is no ring associated with %s' % self)

    def is_positive(self, a):
        """Returns True if `a` is positive. """
        return self.dom.is_positive(a.LC())

    def is_negative(self, a):
        """Returns True if `a` is negative. """
        return self.dom.is_negative(a.LC())

    def is_nonpositive(self, a):
        """Returns True if `a` is non-positive. """
        return self.dom.is_nonpositive(a.LC())

    def is_nonnegative(self, a):
        """Returns True if `a` is non-negative. """
        return self.dom.is_nonnegative(a.LC())

    def numer(self, a):
        """Returns numerator of `a`. """
        return a

    def denom(self, a):
        """Returns denominator of `a`. """
        return self.one

class PolynomialRing(Ring):
    """A class for representing multivariate polynomial rings. """

    dtype        = DMP
    is_Poly      = True
    is_Composite = True

    has_assoc_Ring         = True
    has_assoc_Field        = True

    has_CharacteristicZero = True

    def __init__(self, dom, *gens):
        if not gens:
            raise GeneratorsNeeded("generators not specified")

        lev = len(gens) - 1

        self.zero = self.dtype.zero(lev, dom)
        self.one  = self.dtype.one(lev, dom)

        self.dom  = dom
        self.gens = gens

    def __str__(self):
        return str(self.dom) + '[' + ','.join(map(str, self.gens)) + ']'

    def __hash__(self):
        return hash((self.__class__.__name__, self.dtype, self.dom, self.gens))

    def __call__(self, a):
        """Construct an element of `self` domain from `a`. """
        return DMP(a, self.dom, len(self.gens)-1)

    def __eq__(self, other):
        """Returns `True` if two algebras are equivalent. """
        if self.dtype == other.dtype:
            return self.gens == other.gens
        else:
            return False

    def __ne__(self, other):
        """Returns `False` if two algebras are equivalent. """
        if self.dtype == other.dtype:
            return self.gens != other.gens
        else:
            return True

    def to_sympy(self, a):
        """Convert `a` to a SymPy object. """
        return basic_from_dict(a.to_sympy_dict(), *self.gens)

    def from_sympy(self, a):
        """Convert SymPy's expression to `dtype`. """
        rep = dict_from_basic(a, self.gens)

        for k, v in rep.iteritems():
            rep[k] = self.dom.from_sympy(v)

        return self(rep)

    def from_ZZ_python(K1, a, K0):
        """Convert a Python `int` object to `dtype`. """
        return K1(K1.dom.convert(a, K0))

    def from_QQ_python(K1, a, K0):
        """Convert a Python `Fraction` object to `dtype`. """
        return K1(K1.dom.convert(a, K0))

    def from_ZZ_sympy(K1, a, K0):
        """Convert a SymPy `Integer` object to `dtype`. """
        return K1(K1.dom.convert(a, K0))

    def from_QQ_sympy(K1, a, K0):
        """Convert a SymPy `Rational` object to `dtype`. """
        return K1(K1.dom.convert(a, K0))

    def from_ZZ_gmpy(K1, a, K0):
        """Convert a GMPY `mpz` object to `dtype`. """
        return K1(K1.dom.convert(a, K0))

    def from_QQ_gmpy(K1, a, K0):
        """Convert a GMPY `mpq` object to `dtype`. """
        return K1(K1.dom.convert(a, K0))

    def from_RR_sympy(K1, a, K0):
        """Convert a SymPy `Real` object to `dtype`. """
        return K1(K1.dom.convert(a, K0))

    def from_RR_mpmath(K1, a, K0):
        """Convert a mpmath `mpf` object to `dtype`. """
        return K1(K1.dom.convert(a, K0))

    def from_PolynomialRing(K1, a, K0):
        """Convert a `DMP` object to `dtype`. """
        if K1.gens == K0.gens:
            if K1.dom == K0.dom:
                return a
            else:
                return a.convert(K1.dom)
        else:
            monoms, coeffs = _dict_reorder(a.to_dict(), K0.gens, K1.gens)

            if K1.dom != K0.dom:
                coeffs = [ K1.dom.convert(c, K0.dom) for c in coeffs ]

            return K1(dict(zip(monoms, coeffs)))

    def from_FractionField(K1, a, K0):
        """Convert a `DMF` object to `dtype`. """
        return

    def get_field(self):
        """Returns a field associated with `self`. """
        return FractionField(self.dom, *self.gens)

    def poly_ring(self, *gens):
        """Returns a polynomial ring, i.e. `K[X]`. """
        raise NotImplementedError('nested domains not allowed')

    def frac_field(self, *gens):
        """Returns a fraction field, i.e. `K(X)`. """
        raise NotImplementedError('nested domains not allowed')

    def is_positive(self, a):
        """Returns True if `LC(a)` is positive. """
        return self.dom.is_positive(a.LC())

    def is_negative(self, a):
        """Returns True if `LC(a)` is negative. """
        return self.dom.is_negative(a.LC())

    def is_nonpositive(self, a):
        """Returns True if `LC(a)` is non-positive. """
        return self.dom.is_nonpositive(a.LC())

    def is_nonnegative(self, a):
        """Returns True if `LC(a)` is non-negative. """
        return self.dom.is_nonnegative(a.LC())

    def gcdex(self, a, b):
        """Extended GCD of `a` and `b`. """
        return a.gcdex(b)

    def gcd(self, a, b):
        """Returns GCD of `a` and `b`. """
        return a.gcd(b)

    def lcm(self, a, b):
        """Returns LCM of `a` and `b`. """
        return a.lcm(b)

    def factorial(self, a):
        """Returns factorial of `a`. """
        return self.dtype(self.dom.factorial(a))

class FractionField(Field):
    """A class for representing rational function fields. """

    dtype        = DMF
    is_Frac      = True
    is_Composite = True

    has_assoc_Ring         = True
    has_assoc_Field        = True

    has_CharacteristicZero = True

    def __init__(self, dom, *gens):
        if not gens:
            raise GeneratorsNeeded("generators not specified")

        lev = len(gens) - 1

        self.zero = self.dtype.zero(lev, dom)
        self.one  = self.dtype.one(lev, dom)

        self.dom  = dom
        self.gens = gens

    def __str__(self):
        return str(self.dom) + '(' + ','.join(map(str, self.gens)) + ')'

    def __hash__(self):
        return hash((self.__class__.__name__, self.dtype, self.dom, self.gens))

    def __call__(self, a):
        """Construct an element of `self` domain from `a`. """
        return DMF(a, self.dom, len(self.gens)-1)

    def __eq__(self, other):
        """Returns `True` if two algebras are equivalent. """
        if self.dtype == other.dtype:
            return self.gens == other.gens
        else:
            return False

    def __ne__(self, other):
        """Returns `False` if two algebras are equivalent. """
        if self.dtype == other.dtype:
            return self.gens != other.gens
        else:
            return True

    def to_sympy(self, a):
        """Convert `a` to a SymPy object. """
        return (basic_from_dict(a.numer().to_sympy_dict(), *self.gens) /
                basic_from_dict(a.denom().to_sympy_dict(), *self.gens))

    def from_sympy(self, a):
        """Convert SymPy's expression to `dtype`. """
        p, q = a.as_numer_denom()

        num = dict_from_basic(p, self.gens)
        den = dict_from_basic(q, self.gens)

        for k, v in num.iteritems():
            num[k] = self.dom.from_sympy(v)

        for k, v in den.iteritems():
            den[k] = self.dom.from_sympy(v)

        return self((num, den)).cancel()

    def from_ZZ_python(K1, a, K0):
        """Convert a Python `int` object to `dtype`. """
        return K1(K1.dom.convert(a, K0))

    def from_QQ_python(K1, a, K0):
        """Convert a Python `Fraction` object to `dtype`. """
        return K1(K1.dom.convert(a, K0))

    def from_ZZ_sympy(K1, a, K0):
        """Convert a SymPy `Integer` object to `dtype`. """
        return K1(K1.dom.convert(a, K0))

    def from_QQ_sympy(K1, a, K0):
        """Convert a SymPy `Rational` object to `dtype`. """
        return K1(K1.dom.convert(a, K0))

    def from_ZZ_gmpy(K1, a, K0):
        """Convert a GMPY `mpz` object to `dtype`. """
        return K1(K1.dom.convert(a, K0))

    def from_QQ_gmpy(K1, a, K0):
        """Convert a GMPY `mpq` object to `dtype`. """
        return K1(K1.dom.convert(a, K0))

    def from_RR_sympy(K1, a, K0):
        """Convert a SymPy `Real` object to `dtype`. """
        return K1(K1.dom.convert(a, K0))

    def from_RR_mpmath(K1, a, K0):
        """Convert a mpmath `mpf` object to `dtype`. """
        return K1(K1.dom.convert(a, K0))

    def from_PolynomialRing(K1, a, K0):
        """Convert a `DMP` object to `dtype`. """
        if K1.gens == K0.gens:
            if K1.dom == K0.dom:
                return K1(a.rep)
            else:
                return K1(a.convert(K1.dom).rep)

    def from_FractionField(K1, a, K0):
        """Convert a `DMF` object to `dtype`. """
        if K1.gens == K0.gens:
            if K1.dom == K0.dom:
                return a
            else:
                return K1(a.numer().convert(K1.dom).rep,
                          a.denom().convert(K1.dom).rep)

    def get_ring(self):
        """Returns a ring associated with `self`. """
        return PolynomialRing(self.dom, *self.gens)

    def poly_ring(self, *gens):
        """Returns a polynomial ring, i.e. `K[X]`. """
        raise NotImplementedError('nested domains not allowed')

    def frac_field(self, *gens):
        """Returns a fraction field, i.e. `K(X)`. """
        raise NotImplementedError('nested domains not allowed')

    def is_positive(self, a):
        """Returns True if `a` is positive. """
        return self.dom.is_positive(a.numer().LC())

    def is_negative(self, a):
        """Returns True if `a` is negative. """
        return self.dom.is_negative(a.numer().LC())

    def is_nonpositive(self, a):
        """Returns True if `a` is non-positive. """
        return self.dom.is_nonpositive(a.numer().LC())

    def is_nonnegative(self, a):
        """Returns True if `a` is non-negative. """
        return self.dom.is_nonnegative(a.numer().LC())

    def numer(self, a):
        """Returns numerator of `a`. """
        return a.numer()

    def denom(self, a):
        """Returns denominator of `a`. """
        return a.denom()

    def factorial(self, a):
        """Returns factorial of `a`. """
        return self.dtype(self.dom.factorial(a))

class ExpressionDomain(Field):
    """A class for arbitrary expressions. """

    is_EX = True

    class Expression(object):
        """An arbitrary expression. """

        __slots__ = ['ex']

        def __init__(self, ex):
            if not isinstance(ex, self.__class__):
                self.ex = sympify(ex)
            else:
                self.ex = ex.ex

        def __repr__(f):
            return 'EX(%s)' % repr(f.ex)

        def __str__(f):
            return 'EX(%s)' %str(f.ex)

        def __hash__(self):
            return hash((self.__class__.__name__, self.ex))

        def as_basic(f):
            return f.ex

        def numer(f):
            return EX(f.ex.as_numer_denom()[0])

        def denom(f):
            return EX(f.ex.as_numer_denom()[1])

        def simplify(f, ex):
            from sympy import cancel
            return f.__class__(cancel(ex))

        def __abs__(f):
            return f.__class__(abs(f.ex))

        def __neg__(f):
            return f.__class__(-f.ex)

        def __add__(f, g):
            return f.simplify(f.ex+f.__class__(g).ex)

        def __radd__(f, g):
            return f.simplify(f.__class__(g).ex+f.ex)

        def __sub__(f, g):
            return f.simplify(f.ex-f.__class__(g).ex)

        def __rsub__(f, g):
            return f.simplify(f.__class__(g).ex-f.ex)

        def __mul__(f, g):
            return f.simplify(f.ex*f.__class__(g).ex)

        def __rmul__(f, g):
            return f.simplify(f.__class__(g).ex*f.ex)

        def __pow__(f, n):
            return f.simplify(f.ex**n)

        def __div__(f, g):
            return f.simplify(f.ex/f.__class__(g).ex)

        def __rdiv__(f, g):
            return f.simplify(f.__class__(g).ex/f.ex)

        def __truediv__(f, g):
            return f.simplify(f.ex/f.__class__(g).ex)

        def __rtruediv__(f, g):
            return f.simplify(f.__class__(g).ex/f.ex)

        def __eq__(f, g):
            return f.ex == f.__class__(g).ex

        def __req__(f, g):
            return f.__class__(g).ex == f.ex

        def __ne__(f, g):
            return f.ex != f.__class__(g).ex

        def __rne__(f, g):
            return f.__class__(g).ex != f.ex

        def __nonzero__(f):
            return f.ex != 0

    dtype = Expression

    zero  = Expression(0)
    one   = Expression(1)

    rep   = 'EX'

    has_assoc_Ring         = False
    has_assoc_Field        = True

    has_CharacteristicZero = True

    def __init__(self):
        pass

    def to_sympy(self, a):
        """Convert `a` to a SymPy object. """
        return a.as_basic()

    def from_sympy(self, a):
        """Convert SymPy's expression to `dtype`. """
        return self.dtype(a)

    def from_ZZ_python(K1, a, K0):
        """Convert a Python `int` object to `dtype`. """
        return K1(K0.to_sympy(a))

    def from_QQ_python(K1, a, K0):
        """Convert a Python `Fraction` object to `dtype`. """
        return K1(K0.to_sympy(a))

    def from_ZZ_sympy(K1, a, K0):
        """Convert a SymPy `Integer` object to `dtype`. """
        return K1(K0.to_sympy(a))

    def from_QQ_sympy(K1, a, K0):
        """Convert a SymPy `Rational` object to `dtype`. """
        return K1(K0.to_sympy(a))

    def from_ZZ_gmpy(K1, a, K0):
        """Convert a GMPY `mpz` object to `dtype`. """
        return K1(K0.to_sympy(a))

    def from_QQ_gmpy(K1, a, K0):
        """Convert a GMPY `mpq` object to `dtype`. """
        return K1(K0.to_sympy(a))

    def from_RR_sympy(K1, a, K0):
        """Convert a SymPy `Real` object to `dtype`. """
        return K1(K0.to_sympy(a))

    def from_RR_mpmath(K1, a, K0):
        """Convert a mpmath `mpf` object to `dtype`. """
        return K1(K0.to_sympy(a))

    def from_PolynomialRing(K1, a, K0):
        """Convert a `DMP` object to `dtype`. """
        return K1(K0.to_sympy(a))

    def from_FractionField(K1, a, K0):
        """Convert a `DMF` object to `dtype`. """
        return K1(K0.to_sympy(a))

    def from_ExpressionDomain(K1, a, K0):
        """Convert a `EX` object to `dtype`. """
        return a

    def get_ring(self):
        """Returns a ring associated with `self`. """
        raise DomainError('there is no ring associated with %s' % self)

    def get_field(self):
        """Returns a field associated with `self`. """
        return self

    def is_positive(self, a):
        """Returns True if `a` is positive. """
        return a.ex.as_coeff_mul()[0].is_positive

    def is_negative(self, a):
        """Returns True if `a` is negative. """
        return a.ex.as_coeff_mul()[0].is_negative

    def is_nonpositive(self, a):
        """Returns True if `a` is non-positive. """
        return a.ex.as_coeff_mul()[0].is_nonpositive

    def is_nonnegative(self, a):
        """Returns True if `a` is non-negative. """
        return a.ex.as_coeff_mul()[0].is_nonnegative

    def numer(self, a):
        """Returns numerator of `a`. """
        return a.numer()

    def denom(self, a):
        """Returns denominator of `a`. """
        return a.denom()

EX = ExpressionDomain()

