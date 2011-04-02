from sympy.core.symbol import Dummy
from sympy.core.add import Add
from sympy.core.mul import Mul
from sympy.core import S
from sympy.core.sympify import sympify
from sympy.core.numbers import Rational

from sympy.ntheory import divisors
from sympy.functions import exp, sqrt, re, im

from sympy.polys.polytools import Poly, cancel, factor
from sympy.polys.polyerrors import PolynomialError, GeneratorsNeeded
from sympy.polys.rationaltools import together

from sympy.simplify import simplify
from sympy.utilities import all

def roots_linear(f):
    """Returns a list of roots of a linear polynomial."""
    r = -f.nth(0)/f.nth(1)
    dom = f.get_domain()

    if not dom.is_Numerical:
        if dom.is_Composite:
            r = factor(together(r))
        else:
            r = simplify(r)

    return [r]

def roots_quadratic(f):
    """Returns a list of roots of a quadratic polynomial."""
    a, b, c = f.all_coeffs()
    dom = f.get_domain()

    def _simplify(expr):
        if dom.is_Composite:
            return factor(together(expr)) # XXX: fix factor
        else:
            return simplify(expr)

    if c is S.Zero:
        r0, r1 = S.Zero, -b/a

        if not dom.is_Numerical:
            r1 = _simplify(r1)
    elif b is S.Zero:
        r = -c/a

        if not dom.is_Numerical:
            R = sqrt(_simplify(r))
        else:
            R = sqrt(r)

        r0 =  R
        r1 = -R
    else:
        d = b**2 - 4*a*c

        if dom.is_Numerical:
            D = sqrt(d)

            r0 = (-b + D) / (2*a)
            r1 = (-b - D) / (2*a)
        else:
            D = sqrt(_simplify(d))
            A = 2*a

            E = _simplify(-b/A)
            F = D/A

            r0 = E + F
            r1 = E - F

    return sorted([r0, r1])

def roots_cubic(f):
    """Returns a list of roots of a cubic polynomial."""
    _, a, b, c = f.monic().all_coeffs()

    if c is S.Zero:
        x1, x2 = roots([1,a,b], multiple = True)
        return [x1, S.Zero, x2]

    p = b - a**2/3
    q = c - a*b/3 + 2*a**3/27

    pon3 = p/3
    aon3 = a/3

    if p is S.Zero:
        if q is S.Zero:
            return [-aon3]*3
        else:
            u1 = q**Rational(1, 3)
    elif q is S.Zero:
        y1, y2 = roots([1, 0, p], multiple=True)
        return [tmp - aon3 for tmp in [y1, S.Zero, y2]]
    else:
        u1 = (q/2 + sqrt(q**2/4 + pon3**3))**Rational(1, 3)

    coeff = S.ImaginaryUnit*sqrt(3)/2

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

       Although there is a general solution, simpler results can be obtained for
       certain values of the coefficients. In all cases, 4 roots are returned:

         1) `f = c + a*(a**2/8 - b/2) == 0`
         2) `g = d - a*(a*(3*a**2/256 - b/16) + c/4) = 0`
         3) if `f != 0` and `g != 0` and `p = -d + a*c/4 - b**2/12` then
           a) `p == 0`
           b) `p != 0`

       Example::

           >>> from sympy import Poly, symbols, I
           >>> from sympy.polys.polyroots import roots_quartic

           >>> r = roots_quartic(Poly('x**4-6*x**3+17*x**2-26*x+20'))

           >>> # 4 complex roots: 1+-I*sqrt(3), 2+-I
           >>> sorted(str(tmp.evalf(n=2)) for tmp in r)
           ['1.0 + 1.7*I', '1.0 - 1.7*I', '2.0 + I', '2.0 - 1.0*I']

       References
       ==========

       .. [1] http://mathforum.org/dr.math/faq/faq.cubic.equations.html
       .. [2] http://en.wikipedia.org/wiki/Quartic_function#
                     Summary_of_Ferrari.27s_method
       .. [3] http://planetmath.org/encyclopedia/
                     GaloisTheoreticDerivationOfTheQuarticFormula.html
       .. [4] http://staff.bath.ac.uk/masjhd/JHD-CA.pdf
       .. [5] http://www.albmath.org/files/Math_5713.pdf
       .. [6] http://www.statemaster.com/encyclopedia/Quartic-equation

    """
    _, a, b, c, d = f.monic().all_coeffs()

    if not d:
        return [S.Zero] + roots([1, a, b, c], multiple=True)
    elif (c/a)**2 == d:
        x, m = f.gen, c/a

        g = Poly(x**2 + a*x + b - 2*m, x)

        z1, z2 = roots_quadratic(g)

        h1 = Poly(x**2 - z1*x + m, x)
        h2 = Poly(x**2 - z2*x + m, x)

        r1 = roots_quadratic(h1)
        r2 = roots_quadratic(h2)

        return r1 + r2
    else:
        a2 = a**2
        e = b - 3*a2/8
        f = c + a*(a2/8 - b/2)
        g = d - a*(a*(3*a2/256 - b/16) + c/4)
        aon4 = a/4
        ans = []

        if f is S.Zero:
            y1, y2 = [tmp**S.Half for tmp in
                      roots([1, e, g], multiple = True)]
            return [tmp - aon4 for tmp in [-y1, -y2, y1, y2]]
        if g is S.Zero:
            y = [S.Zero] + roots([1, 0, e, f], multiple = True)
            return [tmp - aon4 for tmp in y]
        else:
            p = -e**2/12 - g
            q = -e**3/108 + e*g/3 - f**2/8
            TH = Rational(1, 3)
            if p is S.Zero:
                y = -5*e/6 - q**TH
            else:
                # with p !=0 then u below is not 0
                root = sqrt(q**2/4 + p**3/27)
                r = -q/2 + root # or -q/2 - root
                u = r**TH # primary root of solve(x**3-r, x)
                y = -5*e/6 + u - p/u/3
            w = sqrt(e + 2*y)
            arg1 = 3*e + 2*y
            arg2 = 2*f/w
            for s in [-1, 1]:
                root = sqrt(-(arg1 + s*arg2))
                for t in [-1, 1]:
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

    if all([ r.is_number for r in roots ]):
        reals, complexes = [], []

        for root in roots:
            if root.is_real:
                reals.append(root)
            else:
                complexes.append(root)

        roots = sorted(reals) + sorted(complexes, key=lambda r: (re(r), -im(r)))

    return roots

def roots_rational(f):
    """Returns a list of rational roots of a polynomial."""
    domain = f.get_domain()

    if domain.is_QQ:
        _, f = f.clear_denoms()
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
    flags = dict(flags)

    auto = flags.pop('auto', True)
    cubics = flags.pop('cubics', True)
    quartics = flags.pop('quartics', True)
    multiple = flags.pop('multiple', False)
    filter = flags.pop('filter', None)
    predicate = flags.pop('predicate', None)

    if isinstance(f, list):
        if gens:
            raise ValueError('redundant generators given')

        x = Dummy('x')

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

        if auto and f.get_domain().has_Ring:
            f = f.to_field()

    x = f.gen

    def _update_dict(result, root, k):
        if root in result:
            result[root] += k
        else:
            result[root] = k

    def _try_decompose(f):
        """Find roots using functional decomposition. """
        factors, roots = f.decompose(), []

        for root in _try_heuristics(factors[0]):
            roots.append(root)

        for factor in factors[1:]:
            previous, roots = list(roots), []

            for root in previous:
                g = factor - Poly(root, x)

                for root in _try_heuristics(g):
                    roots.append(root)

        return roots

    def _try_heuristics(f):
        """Find roots using formulas and some tricks. """
        if f.is_ground:
            return []
        if f.is_monomial:
            return [S(0)]*f.degree()

        if f.length() == 2:
            if f.degree() == 1:
                return map(cancel, roots_linear(f))
            else:
                return roots_binomial(f)

        result = []

        for i in [-1, 1]:
            if not f.eval(i):
                f = f.exquo(Poly(x - i, x))
                result.append(i)
                break

        n = f.degree()

        if n == 1:
            result += map(cancel, roots_linear(f))
        elif n == 2:
            result += map(cancel, roots_quadratic(f))
        elif n == 3 and cubics:
            result += roots_cubic(f)
        elif n == 4 and quartics:
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

        if f.degree() == 1:
            result[roots_linear(f)[0]] = 1
        elif f.degree() == 2:
            for r in roots_quadratic(f):
                _update_dict(result, r, 1)
        elif f.length() == 2:
            for r in roots_binomial(f):
                _update_dict(result, r, 1)
        else:
            _, factors = Poly(f.as_basic()).factor_list()

            if len(factors) == 1 and factors[0][1] == 1:
                for root in _try_decompose(f):
                    _update_dict(result, root, 1)
            else:
                for factor, k in factors:
                    for r in _try_heuristics(Poly(factor, x, field=True)):
                        _update_dict(result, r, k)

        result.update(zeros)

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

    if predicate is not None:
        for zero in dict(result).iterkeys():
            if not predicate(zero):
                del result[zero]

    if not multiple:
        return result
    else:
        zeros = []

        for zero, k in result.iteritems():
            zeros.extend([zero]*k)

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
    args = dict(args)
    filter = args.pop('filter', None)

    F = Poly(f, *gens, **args)

    if not F.is_Poly:
        return [f]

    if F.is_multivariate:
        raise ValueError('multivariate polynomials not supported')

    x = F.gens[0]

    zeros = roots(F, filter=filter)

    if not zeros:
        factors = [F]
    else:
        factors, N = [], 0

        for r, n in zeros.iteritems():
            factors, N = factors + [Poly(x-r, x)]*n, N + n

        if N < F.degree():
            G = reduce(lambda p,q: p*q, factors)
            factors.append(F.exquo(G))

    if not isinstance(f, Poly):
        return [ f.as_basic() for f in factors ]
    else:
        return factors

