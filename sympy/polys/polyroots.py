from sympy.core.symbol import Symbol
from sympy.core.add import Add
from sympy.core.mul import Mul
from sympy.core.basic import Basic, S
from sympy.core.sympify import sympify
from sympy.core.numbers import Rational

from sympy.ntheory import divisors
from sympy.functions import exp, sqrt

from sympy.polys import (
    Poly, cancel, PolynomialError, GeneratorsNeeded,
)

def roots_linear(f):
    """Returns a list of roots of a linear polynomial."""
    return [-f.nth(0)/f.nth(1)]

def roots_quadratic(f):
    """Returns a list of roots of a quadratic polynomial."""
    a, b, c = f.all_coeffs()

    if c is S.Zero:
        return [c, -b/a]

    d = ((b**2).expand() - 4*a*c)**S.Half

    roots = [
        (-b + d) / (2*a),
        (-b - d) / (2*a),
    ]

    return roots

def roots_cubic(f):
    """Returns a list of roots of a cubic polynomial."""
    one, a, b, c = f.monic().all_coeffs()

    if c is S.Zero:
        x1, x2 = roots([1,a,b], multiple = True)
        return [x1, S.Zero, x2]

    p = b - a**2/3
    q = c - a*b/3 + 2*a**3/27

    pon3 = p/3
    aon3 = a/3

    if p is S.Zero:
        if q is S.Zero:
            return [-aon3] * 3
        else:
            u1 = q**Rational(1, 3)
    elif q is S.Zero:
        y1, y2 = roots([1, 0, p], multiple=True)
        return [tmp - aon3 for tmp in [y1, S.Zero, y2]]
    else:
        u1 = (q/2 + (q**2/4 + pon3**3)**S.Half)**Rational(1, 3)

    coeff = S.ImaginaryUnit*3**S.Half / 2

    u2 = u1*(-S.Half + coeff)
    u3 = u1*(-S.Half - coeff)

    soln = [
        -u1 + pon3/u1 - aon3,
        -u2 + pon3/u2 - aon3,
        -u3 + pon3/u3 - aon3
    ]

    return soln

def roots_quartic(f):
    r"""Returns a list of roots of a quartic polynomial.

       There are many references for solving quartic expressions available [1-5].
       This reviewer has found that many of them require one to select from among
       2 or more possible sets of solutions and that some solutions work when one
       is searching for real roots but don't work when searching for complex roots
       (though this is not always stated clearly). The following routine has been
       tested and found to be correct for 0, 2 or 4 complex roots.

       The quasisymmetric case solution [6] looks for quartics that have the form
       `x**4 + A*x**3 + B*x**2 + C*x + D = 0` where `(C/A)**2 = D`.

       NOTE: There is not a single symbolic solution that is valid for all
       possible values of `A`, `B`, `C` and `D`. There are 4 sets of solutions
       possible based on the code below. These solutions (determined by the values
       of the reduced quartic coefficients, `a = B/A`, `b = C/A`, `c = D/A` and
       `d = E/A`, are:

         1) `f = c + a * (a**2 / 8 - b / 2) == 0`
         2) `g = d - a * (a * (3 * a**2 / 256 - b / 16) + c / 4) = 0`
         3) if `f != 0` and `g != 0` but
           a) `p = -d + a*c/4 - b**2/12 = 0` and
              `q = b*d/3 + a*b*c/24 - c**2/8 - d*a**2/8 - b**3/108 >= 0`
              then `u` (see code) will be zero, otherwise
           b) `u != 0`

               Schematically, it looks like this::

                   f = 0    g = 0           f != 0 and g != 0
                     |        |                   /   \
                     |        |       p=0 and q>=0     p!=0 or q<0
                     |        |       (i.e. u = 0     (i.e. u != 0)
                     |        |            |                |
                   4 solns  4 solns      4 solns          4 solns
                                                (default symbolic solution)

       These branches do not count the special cases that have a particularly
       simple form of the roots. Those special cases can often be solved by the
       general procedure. In the test suite, there are tests for those cases,
       and each of them marked with "general soln ok, too" in the code below
       still gave the same for the tests.

       Example::

           >>> from sympy import Poly
           >>> from sympy.polys.polyroots import roots_quartic

           >>> r = roots_quartic(Poly('x**4-6*x**3+17*x**2-26*x+20'))

           >>> # 4 complex roots: 1+-I*sqrt(3), 2+-I
           >>> sorted(str(tmp.evalf(n=2)) for tmp in r)
           ['1.0 + 1.7*I', '1.0 - 1.7*I', '2.0 + I', '2.0 - 1.0*I']

       References
       ==========

       .. [1] http://mathforum.org/dr.math/faq/faq.cubic.equations.html
       .. [2] http://en.wikipedia.org/wiki/Quartic_function#Summary_of_Ferrari.27s_method
       .. [3] http://planetmath.org/encyclopedia/GaloisTheoreticDerivationOfTheQuarticFormula.html
       .. [4] http://staff.bath.ac.uk/masjhd/JHD-CA.pdf
       .. [5] http://www.albmath.org/files/Math_5713.pdf
       .. [6] http://www.statemaster.com/encyclopedia/Quartic-equation

    """
    _, a, b, c, d = f.monic().all_coeffs()

    if not d:
        return [S.Zero] + roots([1, a, b, c], multiple=True)
    elif (c/a)**2 == d:
        x, m = f.gen, sqrt(d)

        g = Poly(x**2 + a*x + b - 2*m, x)

        z1, z2 = roots_quadratic(g)

        h1 = Poly(x**2 - z1*x + m, x)
        h2 = Poly(x**2 - z2*x + m, x)

        r1 = roots_quadratic(h1)
        r2 = roots_quadratic(h2)

        return r1 + r2
    else:
        a2 = a ** 2
        e = b - 3 * a2 / 8
        f = c + a * (a2 / 8 - b / 2)
        g = d - a * (a * (3 * a2 / 256 - b / 16) + c / 4)
        aon4 = a / 4
        ans = []

        if f.is_zero: # general solution not valid if f = 0.
            y1, y2 = [tmp ** S.Half for tmp in
                      roots([1, e, g], multiple = True)]
            return [tmp - aon4 for tmp in [-y1, -y2, y1, y2]]
        if g.is_zero: # general solution not valid if g = 0
            y = [S.Zero] + roots([1, 0, e, f], multiple = True)
            return [tmp - aon4 for tmp in y]
        else:
            TH = Rational(1, 3)
            p = -e**2/12 - g
            q = -e**3/108 + e*g/3 - f**2/8
            root = sqrt(q**2/4 + p**3/27)
            rr = [-q/2 + s*root for s in [1]] # in [1,-1], either will do, so pick 1
            for r in rr:
                uu = [r**TH] # solve(x**3-r,x), any one will do, so take primary
                for u in uu:
                    if u.is_zero:
                        y = -5*e/6 + u - q**TH
                    else:
                        y = -5*e/6 + u - p/u/3
                    w = sqrt(e + 2*y)
                    # try to return the real solutions first if the
                    # sign can be determined. The term tested is the
                    # argument to `root` below.
                    arg1 = 3*e + 2*y
                    arg2 = 2*f/w
                    if -(arg1 + arg2) > S.Zero:
                        ss = [-1, 1]
                    else:
                        ss= [1, -1]
                    for s in ss:
                        root = sqrt(-(arg1 + s*arg2))
                        # return the more negative root first;
                        # note that t and s have opposite signs
                        # in the formula: s=+/-1 while t=-/+1.
                        if aon4 > S.Zero:
                            tt = [-1, 1]
                        else:
                            tt = [1, -1]
                        for t in tt:
                            ans.append((s*w - t*root)/2 - aon4)
    return ans

def roots_binomial(f):
    """Returns a list of roots of a binomial polynomial."""
    n = f.degree()

    a, b = f.nth(n), f.nth(0)
    alpha = (-cancel(b/a))**Rational(1, n)

    if alpha.is_number:
        alpha = alpha.expand(complex=True)

    roots, I = [], S.ImaginaryUnit

    for k in xrange(n):
        zeta = exp(2*k*S.Pi*I/n).expand(complex=True)
        roots.append((alpha*zeta).expand(power_base=False))

    return roots

def roots_rational(f):
    """Returns a list of rational roots of a polynomial."""
    domain = f.get_domain()

    if domain.is_QQ:
        _, f = f.ground_to_ring()
    elif domain.is_ZZ:
        f = f.set_domain('QQ')
    else:
        return []

    LC_divs = divisors(int(f.LC()))
    EC_divs = divisors(int(f.EC()))

    if not f.eval(S.Zero):
        zeros = [S.Zero]
    else:
        zeros = []

    for p in LC_divs:
        for q in EC_divs:
            zero = Rational(p, q)

            if not f.eval(zero):
                zeros.append(zero)

            if not f.eval(-zero):
                zeros.append(-zero)

    return zeros

def roots(f, *gens, **flags):
    """Computes symbolic roots of a univariate polynomial.

       Given a univariate polynomial f with symbolic coefficients (or
       a list of the polynomial's coefficients), returns a dictionary
       with its roots and their multiplicities.

       Only roots expressible via radicals will be returned.  To get
       a complete set of roots use RootOf class or numerical methods
       instead. By default cubic and quartic formulas are used in
       the algorithm. To disable them because of unreadable output
       set `cubics=False` or `quartics=False` respectively.

       To get roots from a specific domain set the `filter` flag with
       one of the following specifiers: Z, Q, R, I, C. By default all
       roots are returned (this is equivalent to setting `filter='C'`).

       By default a dictionary is returned giving a compact result in
       case of multiple roots.  However to get a tuple containing all
       those roots set the `multiple` flag to True.

       Examples
       ========

           >>> from sympy import Poly, roots
           >>> from sympy.abc import x, y

           >>> roots(x**2 - 1, x)
           {1: 1, -1: 1}

           >>> p = Poly(x**2-1, x)
           >>> roots(p)
           {1: 1, -1: 1}

           >>> p = Poly(x**2-y, x, y)

           >>> roots(Poly(p, x))
           {y**(1/2): 1, -y**(1/2): 1}

           >>> roots(x**2 - y, x)
           {y**(1/2): 1, -y**(1/2): 1}

           >>> roots([1, 0, -1])
           {1: 1, -1: 1}

    """
    multiple = flags.get('multiple', False)

    if isinstance(f, list):
        if gens:
            raise ValueError('redundant generators given')

        x = Symbol('x', dummy=True)

        poly, i = {}, len(f)-1

        for coeff in f:
            poly[i], i = sympify(coeff), i-1

        f = Poly(poly, x, field=True)
    else:
        try:
            f = Poly(f, *gens, **flags)
        except GeneratorsNeeded:
            if multiple:
                return []
            else:
                return {}

        if f.is_multivariate:
            raise PolynomialError('multivariate polynomials are not supported')

        f, x = f.to_field(), f.gen

    def _update_dict(result, root, k):
        if root in result:
            result[root] += k
        else:
            result[root] = k

    def _try_decompose(f):
        """Find roots using functional decomposition. """
        factors = f.decompose()
        result, g = {}, factors[0]

        for h, i in g.sqf_list()[1]:
            for r in _try_heuristics(h):
                _update_dict(result, r, i)

        for factor in factors[1:]:
            last, result = result.copy(), {}

            for last_r, i in last.iteritems():
                g = factor - Poly(last_r, x)

                for h, j in g.sqf_list()[1]:
                    for r in _try_heuristics(h):
                        _update_dict(result, r, i*j)

        return result

    def _try_heuristics(f):
        """Find roots using formulas and some tricks. """
        if f.is_ground:
            return []
        if f.is_monomial:
            return [S(0)] * f.degree()

        if f.length() == 2:
            if f.degree() == 1:
                return map(cancel, roots_linear(f))
            else:
                return roots_binomial(f)

        result = []

        for i in [S(-1), S(1)]:
            if f.eval(i).expand().is_zero:
                f = f.exquo(Poly(x-1, x))
                result.append(i)
                break

        n = f.degree()

        if n == 1:
            result += map(cancel, roots_linear(f))
        elif n == 2:
            result += map(cancel, roots_quadratic(f))
        elif n == 3 and flags.get('cubics', True):
            result += roots_cubic(f)
        elif n == 4 and flags.get('quartics', True):
            result += roots_quartic(f)

        return result

    if f.is_monomial == 1:
        if f.is_ground:
            if multiple:
                return []
            else:
                return {}
        else:
            result = { S(0) : f.degree() }
    else:
        (k,), f = f.terms_gcd()

        if not k:
            zeros = {}
        else:
            zeros = { S(0) : k }

        result = {}

        if f.length() == 2:
            if f.degree() == 1:
                result[cancel(roots_linear(f)[0])] = 1
            else:
                for r in roots_binomial(f):
                    _update_dict(result, r, 1)
        elif f.degree() == 2:
            for r in roots_quadratic(f):
                _update_dict(result, cancel(r), 1)
        else:
            _, factors = Poly(f.as_basic()).factor_list()

            if len(factors) == 1 and factors[0][1] == 1:
                result = _try_decompose(f)
            else:
                for factor, k in factors:
                    for r in _try_heuristics(Poly(factor, x, field=True)):
                        _update_dict(result, r, k)

        result.update(zeros)

    filter = flags.get('filter', None)

    if filter not in [None, 'C']:
        handlers = {
            'Z' : lambda r: r.is_Integer,
            'Q' : lambda r: r.is_Rational,
            'R' : lambda r: r.is_real,
            'I' : lambda r: r.is_imaginary,
        }

        try:
            query = handlers[filter]
        except KeyError:
            raise ValueError("Invalid filter: %s" % filter)

        for zero in dict(result).iterkeys():
            if not query(zero):
                del result[zero]

    predicate = flags.get('predicate', None)

    if predicate is not None:
        for zero in dict(result).iterkeys():
            if not predicate(zero):
                del result[zero]

    if not multiple:
        return result
    else:
        zeros = []

        for zero, k in result.iteritems():
            zeros.extend([zero] * k)

        return zeros

def root_factors(f, *gens, **args):
    """Returns all factors of a univariate polynomial.

       Examples
       ========

           >>> from sympy.abc import x, y
           >>> from sympy.polys.polyroots import root_factors

           >>> root_factors(x**2-y, x)
           [x - y**(1/2), x + y**(1/2)]

    """
    F = Poly(f, *gens, **args)

    if not F.is_Poly:
        return [f]

    if F.is_multivariate:
        raise ValueError('multivariate polynomials not supported')

    x = F.gens[0]

    if 'multiple' in args:
        del args['multiple']

    zeros = roots(F, **args)

    if not zeros:
        factors = [F]
    else:
        factors, N = [], 0

        for r, n in zeros.iteritems():
            factors, N = factors + [Poly(x-r, x)]*n, N + n

        if N < F.degree():
            g = reduce(lambda p,q: p*q, factors)
            factors.append(f.exquo(g))

    if not isinstance(f, Poly):
        return [ f.as_basic() for f in factors ]
    else:
        return factors

def number_of_real_roots(f, *gens, **args):
    """Returns the number of distinct real roots of `f` in `(inf, sup]`.

       Examples
       ========

           >>> from sympy import Poly
           >>> from sympy.abc import x, y

           >>> from sympy.polys.polyroots import number_of_real_roots

           >>> f = Poly(x**2 - 1, x)

           Count real roots in the (-oo, oo) interval:

           >>> number_of_real_roots(f)
           2

           Count real roots in the (0, 2) interval:

           >>> number_of_real_roots(f, inf=0, sup=2)
           1

           Count real roots in the (2, oo) interval:

           >>> number_of_real_roots(f, inf=2)
           0

       References
       ==========

       .. [Davenport88] J.H. Davenport, Y. Siret, E. Tournier, Computer
           Algebra Systems and Algorithms for Algebraic Computation,
           Academic Press, London, 1988, pp. 124-128
    """

    def sign_changes(seq):
        count = 0

        for i in xrange(1, len(seq)):
            if (seq[i-1] < 0 and seq[i] >= 0) or \
               (seq[i-1] > 0 and seq[i] <= 0):
                count += 1

        return count

    F = Poly(f, *gens, **args)

    if not F.is_Poly:
        return 0

    if F.is_multivariate:
        raise ValueError('multivariate polynomials not supported')

    if F.degree() < 1:
        return 0

    inf = args.get('inf', None)

    if inf is not None:
        inf = sympify(inf)

        if not inf.is_number:
            raise ValueError("Not a number: %s" % inf)
        elif abs(inf) is S.Infinity:
            inf = None

    sup = args.get('sup', None)

    if sup is not None:
        sup = sympify(sup)

        if not sup.is_number:
            raise ValueError("Not a number: %s" % sup)
        elif abs(sup) is S.Infinity:
            sup = None

    sturm = F.sturm()

    if inf is None:
        signs_inf = sign_changes([ s.LC() * (-1)**s.degree() for s in sturm ])
    else:
        signs_inf = sign_changes([ s.eval(inf) for s in sturm ])

    if sup is None:
        signs_sup = sign_changes([ s.LC() for s in sturm ])
    else:
        signs_sup = sign_changes([ s.eval(sup) for s in sturm ])

    return abs(signs_inf - signs_sup)

_exact_roots_cache = {}

def _exact_roots(f):
    if f in _exact_roots_cache:
        zeros = _exact_roots_cache[f]
    else:
        exact, zeros = roots(f), []

        for zero, k in exact.iteritems():
            zeros += [zero] * k

        _exact_roots_cache[f] = zeros

    return zeros

class RootOf(Basic):
    """Represents n-th root of a univariate polynomial. """

    def __new__(cls, f, index):
        if isinstance(f, RootsOf):
            f = f.poly
        elif not isinstance(f, Poly):
            raise PolynomialError("%s is not a polynomial" % f)

        if f.is_multivariate:
            raise ValueError('multivariate polynomial')

        if index < 0 or index >= f.degree():
            raise IndexError("Index must be in [0, %d] range" % (f.degree()-1))
        else:
            exact = _exact_roots(f)

            if index < len(exact):
                return exact[index]
            else:
                return Basic.__new__(cls, f, index)

    @property
    def poly(self):
        return self._args[0]

    @property
    def index(self):
        return self._args[1]

    def atoms(self, *args, **kwargs):
        return self.poly.atoms(*args, **kwargs)

class RootsOf(Basic):
    """Represents all roots of a univariate polynomial.

       >>> from sympy import roots, RootsOf
       >>> from sympy.abc import x, y

       >>> roots = RootsOf(x**2 + 2, x)

       >>> list(roots.roots())
       [I*2**(1/2), -I*2**(1/2)]

    """

    def __new__(cls, f, x=None):
        if not isinstance(f, Poly):
            f = Poly(f, x)
        elif x is not None:
            raise SymbolsError("Redundant symbols were given")

        if f.is_multivariate:
            raise ValueError('multivariate polynomial')

        return Basic.__new__(cls, f)

    @property
    def poly(self):
        return self._args[0]

    @property
    def count(self):
        return self.poly.degree()

    def roots(self):
        """Iterates over all roots: exact and formal. """
        exact = _exact_roots(self.poly)

        for root in exact:
            yield root

        for j in range(len(exact), self.count):
            yield RootOf(self.poly, j)

    def exact_roots(self):
        """Iterates over exact roots only. """
        exact = _exact_roots(self.poly)

        for root in exact:
            yield root

    def formal_roots(self):
        """Iterates over formal roots only. """
        exact = _exact_roots(self.poly)

        for j in range(len(exact), self.count):
            yield RootOf(self.poly, j)

    def __call__(self, index):
        return RootOf(self.poly, index)

    def atoms(self, *args, **kwargs):
        return self.poly.atoms(*args, **kwargs)

class RootSum(Basic):
    """Represents a sum of all roots of a univariate polynomial. """

    def __new__(cls, f, *args, **flags):
        if not hasattr(f, '__call__'):
            raise TypeError("%s is not a callable object" % f)

        roots = RootsOf(*args)

        if not flags.get('evaluate', True):
            return Basic.__new__(cls, f, roots)
        else:
            if roots.count == 0:
                return S.Zero
            else:
                result = []

                for root in roots.exact_roots():
                    result.append(f(root))

                if len(result) < roots.count:
                    result.append(Basic.__new__(cls, f, roots))

                return Add(*result)

    @property
    def function(self):
        return self._args[0]

    @property
    def roots(self):
        return self._args[1]

    def doit(self, **hints):
        if not hints.get('roots', True):
            return self
        else:
            result = S.Zero

            for root in self.roots.roots():
                result += self.function(root)

            return result

