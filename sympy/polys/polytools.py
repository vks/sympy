"""User-friendly public interface to polynomial functions. """

from sympy import (
    S, Basic, I, Integer, Add, Mul, sympify, ask,
)

from sympy.core.decorators import (
    _sympifyit,
)

from sympy.polys.polyclasses import (
    GFP, DMP, SDP, ANP, DMF,
)

from sympy.polys.polyutils import (
    dict_from_basic,
    basic_from_dict,
    _sort_gens,
    _unify_gens,
    _analyze_gens,
    _dict_reorder,
    _dict_from_basic_no_gens,
)

from sympy.polys.groebnertools import (
    sdp_from_dict, sdp_div, sdp_groebner,
)

from sympy.polys.monomialtools import (
    monomial_cmp,
)

from sympy.polys.polyerrors import (
    OperationNotSupported, DomainError,
    CoercionFailed, UnificationFailed,
    GeneratorsNeeded, PolynomialError,
)

from sympy.mpmath import (
    polyroots as npolyroots,
)

from sympy.utilities import (
    any, all, numbered_symbols,
)

from sympy.ntheory import isprime

import re

_re_dom_poly = re.compile("^(Z|ZZ|Q|QQ)\[(.+)\]$")
_re_dom_frac = re.compile("^(Z|ZZ|Q|QQ)\((.+)\)$")

_re_dom_algebraic = re.compile("^(Q|QQ)\<(.+)\>$")

from sympy.polys.algebratools import Algebra, ZZ, QQ, RR, EX

def _construct_domain(rep, **args):
    """Constructs the minimal domain that the coefficients of `rep` fit in. """
    extension = args.get('extension', None)
    field = args.get('field', False)

    def _construct_simple(rep):
        """Handle ZZ, QQ, RR and algebraic number domains. """
        result, rational, inexact, algebraic = {}, False, False, False

        if extension is True:
            is_algebraic = lambda coeff: ask(coeff, 'algebraic')
        else:
            is_algebraic = lambda coeff: False

        for coeff in rep.itervalues():
            if coeff.is_Rational:
                if not coeff.is_Integer:
                    rational = True
            elif coeff.is_Real:
                if not algebraic:
                    inexact = True
                else:
                    return False
            elif is_algebraic(coeff):
                if not inexact:
                    algebraic = True
                else:
                    return False
            else:
                return None

        if algebraic:
            from numberfields import primitive_element

            monoms, coeffs, exts = [], [], set([])

            for monom, coeff in rep.iteritems():
                if coeff.is_Rational:
                    coeff = (None, 0, QQ.from_sympy(coeff))
                else:
                    a, _ = coeff.as_coeff_factors()
                    coeff -= a

                    b, _ = coeff.as_coeff_terms()
                    coeff /= b

                    exts.add(coeff)

                    a = QQ.from_sympy(a)
                    b = QQ.from_sympy(b)

                    coeff = (coeff, b, a)

                monoms.append(monom)
                coeffs.append(coeff)

            exts = list(exts)

            g, span, H = primitive_element(exts, ex=True, polys=True)
            root = sum([ s*ext for s, ext in zip(span, exts) ])

            K, g = QQ.algebraic_field((g, root)), g.rep.rep

            for monom, (coeff, a, b) in zip(monoms, coeffs):
                if coeff is not None:
                    coeff = a*ANP.from_list(H[exts.index(coeff)], g, QQ) + b
                else:
                    coeff = ANP.from_list([b], g, QQ)

                result[monom] = coeff
        else:
            if inexact:
                K = RR
            else:
                if field or rational:
                    K = QQ
                else:
                    K = ZZ

            for monom, coeff in rep.iteritems():
                result[monom] = K.from_sympy(coeff)

        return K, result

    def _construct_composite(rep):
        """Handle domains like ZZ[X], QQ[X], ZZ(X) or QQ(X). """
        numers, denoms = [], []

        for coeff in rep.itervalues():
            num, den = coeff.as_numer_denom()

            try:
                numers.append(_dict_from_basic_no_gens(num))
            except GeneratorsNeeded:
                numers.append((num, None))

            try:
                denoms.append(_dict_from_basic_no_gens(den))
            except GeneratorsNeeded:
                denoms.append((den, None))

        gens = set([])

        for _, num_gens in numers:
            if num_gens is not None:
                gens.update(num_gens)

        fractions = False

        for _, den_gens in denoms:
            if den_gens is not None:
                gens.update(den_gens)
                fractions = True

        if any(gen.is_number for gen in gens):
            return None

        gens = _sort_gens(gens, **args)
        k, coeffs = len(gens), []

        if not field and not fractions:
            if all(den is S.One for den, _ in denoms):
                K = ZZ.poly_ring(*gens)

                for num, num_gens in numers:
                    if num_gens is not None:
                        num_monoms, num_coeffs = _dict_reorder(num, num_gens, gens)
                    else:
                        num_monoms, num_coeffs = [(0,)*k], [num]

                    num_coeffs = [ K.dom.from_sympy(c) for c in num_coeffs ]
                    coeffs.append(K(dict(zip(num_monoms, num_coeffs))))
            else:
                K = QQ.poly_ring(*gens)

                for (num, num_gens), (den, _) in zip(numers, denoms):
                    if num_gens is not None:
                        num_monoms, num_coeffs = _dict_reorder(num, num_gens, gens)
                        num_coeffs = [ coeff/den for coeff in num_coeffs ]
                    else:
                        num_monoms, num_coeffs = [(0,)*k], [num/den]

                    num_coeffs = [ K.dom.from_sympy(c) for c in num_coeffs ]
                    coeffs.append(K(dict(zip(num_monoms, num_coeffs))))
        else:
            K = ZZ.frac_field(*gens)

            for (num, num_gens), (den, den_gens) in zip(numers, denoms):
                if num_gens is not None:
                    num_monoms, num_coeffs = _dict_reorder(num, num_gens, gens)
                else:
                    num_monoms, num_coeffs = [(0,)*k], [num]

                if den_gens is not None:
                    den_monoms, den_coeffs = _dict_reorder(den, den_gens, gens)
                else:
                    den_monoms, den_coeffs = [(0,)*k], [den]

                num_coeffs = [ K.dom.from_sympy(c) for c in num_coeffs ]
                den_coeffs = [ K.dom.from_sympy(c) for c in den_coeffs ]

                num = dict(zip(num_monoms, num_coeffs))
                den = dict(zip(den_monoms, den_coeffs))

                coeffs.append(K((num, den)))

        return K, dict(zip(rep.keys(), coeffs))

    def _construct_expression(rep):
        """The last resort case, i.e. use EX domain. """
        result, K = {}, EX

        for monom, coeff in rep.iteritems():
            result[monom] = K.from_sympy(coeff)

        return EX, result

    rep = dict(rep)

    for monom, coeff in rep.items():
        rep[monom] = sympify(coeff)

    result = _construct_simple(rep)

    if result is not None:
        if result is not False:
            return result
        else:
            return _construct_expression(rep)
    else:
        result = _construct_composite(rep)

        if result is not None:
            return result
        else:
            return _construct_expression(rep)

def _init_poly_from_dict(dict_rep, *gens, **args):
    """Initialize a Poly given a dict instance. """
    domain = args.get('domain')
    modulus = args.get('modulus')
    symmetric = args.get('symmetric')

    if modulus is not None:
        if len(gens) != 1:
            raise PolynomialError("multivariate polynomials over GF(p) are not supported")
        else:
            return GFP(dict_rep, modulus, domain, symmetric)
    else:
        if domain is not None:
            for k, v in dict_rep.iteritems():
                dict_rep[k] = domain.convert(v)
        else:
            domain, dict_rep = _construct_domain(dict_rep, **args)

        return DMP(dict_rep, domain, len(gens)-1)

def _init_poly_from_list(list_rep, *gens, **args):
    """Initialize a Poly given a list instance. """
    domain = args.get('domain')
    modulus = args.get('modulus')
    symmetric = args.get('symmetric')

    if len(gens) != 1:
        raise PolynomialError("can't create a multivariate polynomial from a list")

    if modulus is not None:
        return GFP(list_rep, modulus, domain, symmetric)
    else:
        if domain is not None:
            rep = map(domain.convert, list_rep)
        else:
            dict_rep = dict(enumerate(reversed(list_rep)))
            domain, rep = _construct_domain(dict_rep, **args)

        return DMP(rep, domain, len(gens)-1)

def _init_poly_from_poly(poly_rep, *gens, **args):
    """Initialize a Poly given a Poly instance. """
    domain = args.get('domain')
    modulus = args.get('modulus')
    symmetric = args.get('symmetric')

    if isinstance(poly_rep.rep, DMP):
        if not gens or poly_rep.gens == gens:
            if domain is not None or modulus is not None:
                rep = poly_rep.rep
            else:
                return poly_rep
        else:
            if set(gens) != set(poly_rep.gens):
                return Poly(poly_rep.as_basic(), *gens, **args)
            else:
                dict_rep = dict(zip(*_dict_reorder(
                    poly_rep.rep.to_dict(), poly_rep.gens, gens)))

                rep = DMP(dict_rep, poly_rep.rep.dom, len(gens)-1)

        if domain is not None:
            rep = rep.convert(domain)

        if modulus is not None:
            if not rep.lev and rep.dom.is_ZZ:
                rep = GFP(rep.rep, modulus, rep.dom, symmetric)
            else:
                raise PolynomialError("can't make GF(p) polynomial out of %s" % rep)
    else:
        if not gens or poly_rep.gens == gens:
            if domain is not None or modulus is not None:
                if modulus is not None:
                    rep = GFP(poly_rep.rep.rep, modulus, poly_rep.rep.dom, symmetric)
                else:
                    rep = poly_rep.rep

                if domain is not None:
                    rep = rep.convert(domain)
            else:
                return poly_rep
        else:
            raise PolynomialError("multivariate polynomials over GF(p) are not supported")

    return (rep, gens or poly_rep.gens)

def _init_poly_from_basic(basic_rep, *gens, **args):
    """Initialize a Poly given a Basic expression. """
    if not gens:
        try:
            dict_rep, gens = dict_from_basic(basic_rep, **args)
        except GeneratorsNeeded:
            return basic_rep
    else:
        dict_rep = dict_from_basic(basic_rep, gens, **args)

    def _dict_set_domain(rep, domain):
        result = {}

        for k, v in rep.iteritems():
            result[k] = domain.from_sympy(v)

        return result

    domain = args.get('domain')
    modulus = args.get('modulus')
    symmetric = args.get('symmetric')

    if modulus is not None:
        if len(gens) > 1:
            raise PolynomialError("multivariate polynomials over GF(p) are not supported")
        else:
            result = GFP(_dict_set_domain(dict_rep, domain), modulus, domain, symmetric)
    else:
        if domain is not None:
            dict_rep = _dict_set_domain(dict_rep, domain)
        else:
            domain, dict_rep = _construct_domain(dict_rep, **args)

        result = DMP(dict_rep, domain, len(gens)-1)

    return result, gens

class Poly(Basic):
    """Generic class for representing polynomials in SymPy. """

    __slots__ = ['rep', 'gens']

    is_Poly = True

    def __new__(cls, rep, *gens, **args):
        """Create a new polynomial instance out of something useful. """
        if len(set(gens)) != len(gens):
            raise PolynomialError("duplicated generators: %s" % str(gens))

        if isinstance(rep, (DMP, GFP)):
            if rep.lev != len(gens)-1 or args:
                raise PolynomialError("invalid arguments to construct a polynomial")
        else:
            order = cls._analyze_order(args)
            domain = cls._analyze_domain(args)
            modulus = cls._analyze_modulus(args)
            extension = cls._analyze_extension(args)

            args = dict(args)

            if domain is not None:
                args['domain'] = domain
            elif modulus is not None:
                args['domain'] = ZZ

            if modulus is not None:
                args['modulus'] = modulus
            if extension is not None:
                args['extension'] = extension

            greedy = args.get('greedy')
            field = args.get('field')

            if order is not None:
                if modulus is not None:
                    raise PolynomialError("'order' keyword is not allowed together with 'modulus'")

                raise NotImplementedError("'order' keyword is not yet implemented")

            if domain is not None:
                if domain.is_Composite and set(domain.gens) & set(gens):
                    raise PolynomialError("ground domain and generators interferes together")

                if modulus is not None and not domain.is_ZZ:
                    raise PolynomialError("'modulus' keyword requires ZZ ground domain")

                if greedy is not None:
                    raise PolynomialError("'domain' keyword in not allowed together with 'greedy'")

                if field is not None:
                    raise PolynomialError("'domain' keyword in not allowed together with 'field'")

            if extension is not None:
                if domain is not None:
                    raise PolynomialError("'extension' keyword is not allowed together with 'domain'")

                if modulus is not None:
                    raise PolynomialError("'extension' keyword is not allowed together with 'modulus'")

                if greedy is not None:
                    raise PolynomialError("'extension' keyword in not allowed together with 'greedy'")

                if field is not None:
                    raise PolynomialError("'extension' keyword in not allowed together with 'field'")

                if extension is not True:
                    args['domain'] = domain = QQ.algebraic_field(*extension)

            symmetric = args.get('symmetric')

            if symmetric is not None and modulus is None:
                raise PolynomialError("'symmetric' keyword only allowed together with 'modulus'")

            if isinstance(rep, (dict, list)):
                if not gens:
                    raise GeneratorsNeeded("can't initialize from %s without generators" % type(rep).__name__)

                if isinstance(rep, dict):
                    rep = _init_poly_from_dict(rep, *gens, **args)
                else:
                    rep = _init_poly_from_list(rep, *gens, **args)
            else:
                rep = sympify(rep)

                if rep.is_Poly:
                    result = _init_poly_from_poly(rep, *gens, **args)
                else:
                    result = _init_poly_from_basic(rep, *gens, **args)

                if type(result) is tuple:
                    rep, gens = result
                else:
                    if result.is_Poly or not args.get('strict', True):
                        return result
                    else:
                        raise GeneratorsNeeded("can't initialize from %s without generators" % rep)

        obj = Basic.__new__(cls)

        obj.rep = rep
        obj.gens = gens

        return obj

    def __getnewargs__(self):
        """Data used by pickling protocol version 2. """
        return (self.rep, self.gens)

    def _hashable_content(self):
        """Allow SymPy to hash Poly instances. """
        return (self.rep, self.gens)

    @property
    def args(self):
        """Don't mess up with the core. """
        return [self.as_basic()]

    @property
    def gen(self):
        """Return principal generator. """
        return self.gens[0]

    def unify(f, g):
        """Make `f` and `g` belong to the same domain. """
        g = sympify(g)

        if not g.is_Poly:
            try:
                return f.rep.dom, f.per, f.rep, f.rep.per(f.rep.dom.from_sympy(g))
            except CoercionFailed:
                raise UnificationFailed("can't unify %s with %s" % (f, g))

        if isinstance(f.rep, DMP) and isinstance(g.rep, DMP):
            gens = _unify_gens(f.gens, g.gens)

            dom, lev = f.rep.dom.unify(g.rep.dom, gens), len(gens)-1

            if f.gens != gens:
                f_monoms, f_coeffs = _dict_reorder(f.rep.to_dict(), f.gens, gens)

                if f.rep.dom != dom:
                    f_coeffs = [ dom.convert(c, f.rep.dom) for c in f_coeffs ]

                F = DMP(dict(zip(f_monoms, f_coeffs)), dom, lev)
            else:
                F = f.rep.convert(dom)

            if g.gens != gens:
                g_monoms, g_coeffs = _dict_reorder(g.rep.to_dict(), g.gens, gens)

                if g.rep.dom != dom:
                    g_coeffs = [ dom.convert(c, g.rep.dom) for c in g_coeffs ]

                G = DMP(dict(zip(g_monoms, g_coeffs)), dom, lev)
            else:
                G = g.rep.convert(dom)
        elif isinstance(f.rep, GFP) and isinstance(g.rep, DMP) and f.gens == g.gens:
            dom, G, F, gens = f.rep.dom, GFP(g.rep.convert(f.rep.dom).rep, f.rep.mod, f.rep.dom, f.rep.sym), f.rep, f.gens
        elif isinstance(f.rep, DMP) and isinstance(g.rep, GFP) and f.gens == g.gens:
            dom, F, G, gens = g.rep.dom, GFP(f.rep.convert(g.rep.dom).rep, g.rep.mod, g.rep.dom, g.rep.sym), g.rep, g.gens
        elif isinstance(f.rep, GFP) and isinstance(g.rep, GFP) and f.gens == g.gens and f.rep.mod == g.rep.mod:
            dom, gens, sym = f.rep.dom.unify(g.rep.dom), f.gens, max(f.rep.sym, g.rep.sym)
            F = GFP(f.rep.convert(dom).rep, f.rep.mod, dom, sym)
            G = GFP(g.rep.convert(dom).rep, g.rep.mod, dom, sym)
        else:
            raise UnificationFailed("can't unify %s with %s" % (f, g))

        def per(rep, dom=dom, gens=gens, remove=None):
            if remove is not None:
                gens = gens[:remove]+gens[remove+1:]

                if not gens:
                    return dom.to_sympy(rep)

            return Poly(rep, *gens)

        return dom, per, F, G

    def per(f, rep, gens=None, remove=None):
        """Create a Poly out of the given representation. """
        if gens is None:
            gens = f.gens

        if remove is not None:
            gens = gens[:remove]+gens[remove+1:]

            if not gens:
                return f.rep.dom.to_sympy(rep)

        return Poly(rep, *gens)

    def unit(f):
        """Return unit of `f`'s polynomial algebra. """
        return f.per(f.rep.unit())

    @classmethod
    def _analyze_order(cls, args):
        """Convert `order` to an internal representation. """
        order = args.get('order')

        if order is not None:
            if isinstance(order, str):
                order = monomial_cmp(order)
            elif not hasattr(order, '__call__'):
                raise ValueError("expected monomial order declaration or a function, got %s" % order)

        return order

    @classmethod
    def _analyze_domain(cls, args):
        """Convert `domain` to an internal representation. """
        domain = args.get('domain')

        if domain is not None:
            domain = cls._parse_domain(domain)

        return domain

    @classmethod
    def _parse_domain(cls, dom):
        """Make an algebra out of a string representation. """
        if isinstance(dom, Algebra):
            return dom

        if isinstance(dom, basestring):
            if dom in ['Z', 'ZZ']:
                return ZZ

            if dom in ['Q', 'QQ']:
                return QQ

            if dom in ['R', 'RR']:
                return RR

            if dom == 'EX':
                return EX

            r = re.match(_re_dom_poly, dom)

            if r is not None:
                ground, gens = r.groups()

                gens = map(sympify, gens.split(','))

                if ground in ['Z', 'ZZ']:
                    return ZZ.poly_ring(*gens)
                else:
                    return QQ.poly_ring(*gens)

            r = re.match(_re_dom_frac, dom)

            if r is not None:
                ground, gens = r.groups()

                gens = map(sympify, gens.split(','))

                if ground in ['Z', 'ZZ']:
                    return ZZ.frac_field(*gens)
                else:
                    return QQ.frac_field(*gens)

            r = re.match(_re_dom_algebraic, dom)

            if r is not None:
                gens = map(sympify, r.groups()[1].split(','))
                return QQ.algebraic_field(*gens)

        raise ValueError('expected a valid domain specification, got %s' % dom)

    def set_domain(f, domain):
        """Set the ground domain of `f`. """
        return f.per(f.rep.convert(f._parse_domain(domain)))

    def get_domain(f):
        """Get the ground domain of `f`. """
        return f.rep.dom

    @classmethod
    def _analyze_modulus(cls, args):
        """Convert `modulus` to an internal representation. """
        modulus = args.get('modulus')

        if modulus is not None:
            modulus = cls._parse_modulus(modulus)

        return modulus

    @classmethod
    def _parse_modulus(cls, modulus):
        """Check if we were given a valid modulus. """
        if isinstance(modulus, (int, Integer)) and isprime(modulus):
            return int(modulus)
        else:
            raise ValueError("modulus must be a prime integer, got %s" % modulus)

    def set_modulus(f, modulus):
        """Set the modulus of `f`. """
        modulus = f._parse_modulus(modulus)

        if isinstance(f.rep, GFP):
            return f.per(f.rep.trunc(modulus))
        elif f.rep.dom.is_ZZ and f.is_univariate:
            return f.per(GFP(f.rep.rep, modulus, f.rep.dom))
        else:
            raise PolynomialError("not a polynomial over a Galois field")

    def get_modulus(f):
        """Get the modulus of `f`. """
        if isinstance(f.rep, GFP):
            return Integer(f.rep.mod)
        else:
            raise PolynomialError("not a polynomial over a Galois field")

    @classmethod
    def _analyze_extension(cls, args):
        """Convert `extension` to an internal representation. """
        extension = args.get('extension')
        gaussian = args.get('gaussian')
        split = args.get('split')

        if extension is not None:
            if gaussian is not None:
                raise PolynomialError("'extension' is not allowed together with 'gaussian'")

            if split is not None:
                raise PolynomialError("'extension' is not allowed together with 'split'")

            if isinstance(extension, bool):
                if extension is False:
                    extension = None
            else:
                if not hasattr(extension, '__iter__'):
                    extension = set([extension])
                else:
                    if not extension:
                        extension = None
                    else:
                        extension = set(extension)
        elif gaussian is not None:
            if split is not None:
                raise PolynomialError("'gaussian' is not allowed together with 'split'")
            elif gaussian:
                extension = set([S.ImaginaryUnit])
        elif split is not None:
            raise NotImplementedError('splitting extensions are not supported')

        return extension

    def replace(f, x, y=None):
        """Replace `x` with `y` in generators list. """
        if y is None:
            if f.is_univariate:
                x, y = f.gen, x
            else:
                raise PolynomialError("syntax supported only in univariate case")

        if x == y:
            return f

        if x in f.gens and y not in f.gens:
            dom = f.get_domain()

            if not dom.is_Composite or y not in dom.gens:
                gens = list(f.gens)
                gens[gens.index(x)] = y
                return f.per(f.rep, gens=gens)

        raise PolynomialError("can't replace %s with %s in %s" % (x, y, f))

    def reorder(f, *gens, **args):
        """Efficiently apply new order of generators. """
        if not gens:
            gens = _sort_gens(f.gens, **args)
        elif set(f.gens) != set(gens):
            raise PolynomialError("generators list can differ only up to order of elements")

        rep = dict(zip(*_dict_reorder(f.rep.to_dict(), f.gens, gens)))

        return f.per(DMP(rep, f.rep.dom, len(gens)-1), gens=gens)

    def to_ring(f):
        """Make the ground domain a ring. """
        try:
            result = f.rep.to_ring()
        except AttributeError: # pragma: no cover
            raise OperationNotSupported(f, 'to_ring')

        return f.per(result)

    def to_field(f):
        """Make the ground domain a field. """
        try:
            result = f.rep.to_field()
        except AttributeError: # pragma: no cover
            raise OperationNotSupported(f, 'to_field')

        return f.per(result)

    def coeffs(f):
        """Returns all non-zero coefficients from `f` in lex order. """
        return [ f.rep.dom.to_sympy(c) for c in f.rep.coeffs() ]

    def monoms(f):
        """Returns all non-zero monomials from `f` in lex order. """
        return f.rep.monoms()

    def terms(f):
        """Returns all non-zero terms from `f` in lex order. """
        return [ (m, f.rep.dom.to_sympy(c)) for m, c in f.rep.terms() ]

    def all_coeffs(f):
        """Returns all coefficients from a univariate polynomial `f`. """
        return [ f.rep.dom.to_sympy(c) for c in f.rep.all_coeffs() ]

    def all_monoms(f):
        """Returns all monomials from a univariate polynomial `f`. """
        return f.rep.all_monoms()

    def all_terms(f):
        """Returns all terms from a univariate polynomial `f`. """
        return [ (m, f.rep.dom.to_sympy(c)) for m, c in f.rep.all_terms() ]

    def length(f):
        """Returns the number of non-zero terms in `f`. """
        return len(f.as_dict())

    def as_dict(f):
        """Switch to a dict representation with SymPy coefficients. """
        return f.rep.to_sympy_dict()

    def as_basic(f, *gens):
        """Convert a polynomial instance to a SymPy expression. """
        return basic_from_dict(f.rep.to_sympy_dict(), *(gens or f.gens))

    def lift(f):
        """Convert algebraic coefficients to rationals. """
        try:
            result = f.rep.lift()
        except AttributeError: # pragma: no cover
            raise OperationNotSupported(f, 'lift')

        return f.per(result)

    def deflate(f):
        """Reduce degree of `f` by mapping `x_i**m` to `y_i`. """
        try:
            J, result = f.rep.deflate()
        except AttributeError: # pragma: no cover
            raise OperationNotSupported(f, 'deflate')

        return J, f.per(result)

    def terms_gcd(f):
        """Remove GCD of terms from the polynomial `f`. """
        try:
            J, result = f.rep.terms_gcd()
        except AttributeError: # pragma: no cover
            raise OperationNotSupported(f, 'terms_gcd')

        return J, f.per(result)

    def abs(f):
        """Make all coefficients in `f` positive. """
        try:
            result = f.rep.abs()
        except AttributeError: # pragma: no cover
            raise OperationNotSupported(f, 'abs')

        return f.per(result)

    def neg(f):
        """Negate all cefficients in `f`. """
        try:
            result = f.rep.neg()
        except AttributeError: # pragma: no cover
            raise OperationNotSupported(f, 'neg')

        return f.per(result)

    def add(f, g):
        """Add two polynomials `f` and `g`. """
        _, per, F, G = f.unify(g)

        try:
            result = F.add(G)
        except AttributeError: # pragma: no cover
            raise OperationNotSupported(f, 'add')

        return per(result)

    def sub(f, g):
        """Subtract two polynomials `f` and `g`. """
        _, per, F, G = f.unify(g)

        try:
            result = F.sub(G)
        except AttributeError: # pragma: no cover
            raise OperationNotSupported(f, 'sub')

        return per(result)

    def mul(f, g):
        """Multiply two polynomials `f` and `g`. """
        _, per, F, G = f.unify(g)

        try:
            result = F.mul(G)
        except AttributeError: # pragma: no cover
            raise OperationNotSupported(f, 'mul')

        return per(result)

    def sqr(f):
        """Square a polynomial `f`. """
        try:
            result = f.rep.sqr()
        except AttributeError: # pragma: no cover
            raise OperationNotSupported(f, 'sqr')

        return f.per(result)

    def pow(f, n):
        """Raise `f` to a non-negative power `n`. """
        n = int(n)

        try:
            result = f.rep.pow(n)
        except AttributeError: # pragma: no cover
            raise OperationNotSupported(f, 'pow')

        return f.per(result)

    def pdiv(f, g):
        """Polynomial pseudo-division of `f` by `g`. """
        _, per, F, G = f.unify(g)

        try:
            q, r = F.pdiv(G)
        except AttributeError: # pragma: no cover
            raise OperationNotSupported(f, 'pdiv')

        return per(q), per(r)

    def prem(f, g):
        """Polynomial pseudo-remainder of `f` by `g`. """
        _, per, F, G = f.unify(g)

        try:
            result = F.prem(G)
        except AttributeError: # pragma: no cover
            raise OperationNotSupported(f, 'prem')

        return per(result)

    def pquo(f, g):
        """Polynomial pseudo-quotient of `f` by `g`. """
        _, per, F, G = f.unify(g)

        try:
            result = F.pquo(G)
        except AttributeError: # pragma: no cover
            raise OperationNotSupported(f, 'pquo')

        return per(result)

    def pexquo(f, g):
        """Polynomial exact pseudo-quotient of `f` by `g`. """
        _, per, F, G = f.unify(g)

        try:
            result = F.pexquo(G)
        except AttributeError: # pragma: no cover
            raise OperationNotSupported(f, 'pexquo')

        return per(result)

    def div(f, g):
        """Polynomial division with remainder of `f` by `g`. """
        _, per, F, G = f.unify(g)

        try:
            q, r = F.div(G)
        except AttributeError: # pragma: no cover
            raise OperationNotSupported(f, 'div')

        return per(q), per(r)

    def rem(f, g):
        """Computes polynomial remainder of `f` by `g`. """
        _, per, F, G = f.unify(g)

        try:
            result = F.rem(G)
        except AttributeError: # pragma: no cover
            raise OperationNotSupported(f, 'rem')

        return per(result)

    def quo(f, g):
        """Computes polynomial quotient of `f` by `g`. """
        _, per, F, G = f.unify(g)

        try:
            result = F.quo(G)
        except AttributeError: # pragma: no cover
            raise OperationNotSupported(f, 'quo')

        return per(result)

    def exquo(f, g):
        """Computes polynomial exact quotient of `f` by `g`. """
        _, per, F, G = f.unify(g)

        try:
            result = F.exquo(G)
        except AttributeError: # pragma: no cover
            raise OperationNotSupported(f, 'exquo')

        return per(result)

    def _gen_to_level(f, gen):
        """Returns level associated with the given generator. """
        if isinstance(gen, int):
            length = len(f.gens)

            if -length <= gen < length:
                if gen < 0:
                    return length + gen
                else:
                    return gen
            else:
                raise PolynomialError("-%s <= gen < %s expected, got %s" % (length, length, gen))
        else:
            try:
                return list(f.gens).index(sympify(gen))
            except ValueError:
                raise PolynomialError("a valid generator expected, got %s" % gen)

    def degree(f, gen=0):
        """Returns degree of `f` in `x_j`. """
        j = f._gen_to_level(gen)

        try:
            return f.rep.degree(j)
        except AttributeError: # pragma: no cover
            raise OperationNotSupported(f, 'degree')

    def degree_list(f):
        """Returns a list of degrees of `f`. """
        try:
            return f.rep.degree_list()
        except AttributeError: # pragma: no cover
            raise OperationNotSupported(f, 'degree_list')

    def total_degree(f):
        """Returns the total degree of `f`. """
        try:
            return f.rep.total_degree()
        except AttributeError: # pragma: no cover
            raise OperationNotSupported(f, 'total_degree')

    def LC(f):
        """Returns the leading coefficent of `f`. """
        try:
            result = f.rep.LC()
        except AttributeError: # pragma: no cover
            raise OperationNotSupported(f, 'LC')

        return f.rep.dom.to_sympy(result)

    def TC(f):
        """Returns the trailing coefficent of `f`. """
        try:
            result = f.rep.TC()
        except AttributeError: # pragma: no cover
            raise OperationNotSupported(f, 'TC')

        return f.rep.dom.to_sympy(result)

    def EC(f):
        """Returns the last non-zero coefficent of `f`. """
        try:
            return f.coeffs()[-1]
        except AttributeError: # pragma: no cover
            raise OperationNotSupported(f, 'EC')

    def nth(f, *N):
        """Returns the `n`-th coefficient of `f`. """
        try:
            result = f.rep.nth(*map(int, N))
        except AttributeError: # pragma: no cover
            raise OperationNotSupported(f, 'nth')

        return f.rep.dom.to_sympy(result)

    def LM(f):
        """Returns the leading monomial of `f`. """
        return f.monoms()[0]

    def EM(f):
        """Returns the last non-zero monomial of `f`. """
        return f.monoms()[-1]

    def LT(f):
        """Returns the leading term of `f`. """
        return f.terms()[0]

    def ET(f):
        """Returns the last non-zero term of `f`. """
        return f.terms()[-1]

    def max_norm(f):
        """Returns maximum norm of `f`. """
        try:
            result = f.rep.max_norm()
        except AttributeError: # pragma: no cover
            raise OperationNotSupported(f, 'max_norm')

        return f.rep.dom.to_sympy(result)

    def l1_norm(f):
        """Returns l1 norm of `f`. """
        try:
            result = f.rep.l1_norm()
        except AttributeError: # pragma: no cover
            raise OperationNotSupported(f, 'l1_norm')

        return f.rep.dom.to_sympy(result)

    def ground_to_ring(f):
        """Clear denominators, but keep the ground domain. """
        try:
            coeff, result = f.rep.ground_to_ring()
        except AttributeError: # pragma: no cover
            raise OperationNotSupported(f, 'ground_to_ring')

        return f.rep.dom.to_sympy(coeff), f.per(result)

    def integrate(f, *specs, **args):
        """Computes indefinite integral of `f`. """
        if args.get('auto', True):
            f = f.to_field()

        try:
            if not specs:
                return f.per(f.rep.integrate(m=1))

            rep = f.rep

            for spec in specs:
                if type(spec) is tuple:
                    gen, m = spec
                else:
                    gen, m = spec, 1

                rep = rep.integrate(int(m), f._gen_to_level(gen))

            return f.per(rep)
        except AttributeError: # pragma: no cover
            raise OperationNotSupported(f, 'integrate')

    def diff(f, *specs):
        """Computes partial derivative of `f`. """
        try:
            if not specs:
                return f.per(f.rep.diff(m=1))

            rep = f.rep

            for spec in specs:
                if type(spec) is tuple:
                    gen, m = spec
                else:
                    gen, m = spec, 1

                rep = rep.diff(int(m), f._gen_to_level(gen))

            return f.per(rep)
        except AttributeError: # pragma: no cover
            raise OperationNotSupported(f, 'diff')

    def eval(f, a, gen=0):
        """Evaluates `f` at `a` in the given variable. """
        j = f._gen_to_level(gen)

        try:
            result = f.rep.eval(a, j)
        except AttributeError: # pragma: no cover
            raise OperationNotSupported(f, 'eval')

        return f.per(result, remove=j)

    def half_gcdex(f, g, **args):
        """Half extended Euclidean algorithm of `f` and `g`. """
        dom, per, F, G = f.unify(g)

        if args.get('auto', True):
            F, G = F.to_field(), G.to_field()

        try:
            s, h = F.half_gcdex(G)
        except AttributeError: # pragma: no cover
            raise OperationNotSupported(f, 'half_gcdex')

        return per(s), per(h)

    def gcdex(f, g, **args):
        """Extended Euclidean algorithm of `f` and `g`. """
        dom, per, F, G = f.unify(g)

        if args.get('auto', True):
            F, G = F.to_field(), G.to_field()

        try:
            s, t, h = F.gcdex(G)
        except AttributeError: # pragma: no cover
            raise OperationNotSupported(f, 'gcdex')

        return per(s), per(t), per(h)

    def invert(f, g, **args):
        """Invert `f` modulo `g`, if possible. """
        dom, per, F, G = f.unify(g)

        if args.get('auto', True):
            F, G = F.to_field(), G.to_field()

        try:
            result = F.invert(G)
        except AttributeError: # pragma: no cover
            raise OperationNotSupported(f, 'invert')

        return per(result)

    def subresultants(f, g):
        """Computes subresultant PRS sequence of `f` and `g`. """
        _, per, F, G = f.unify(g)

        try:
            result = F.subresultants(G)
        except AttributeError: # pragma: no cover
            raise OperationNotSupported(f, 'subresultants')

        return map(per, result)

    def resultant(f, g):
        """Computes resultant of `f` and `g` via PRS. """
        _, per, F, G = f.unify(g)

        try:
            result = F.resultant(G)
        except AttributeError: # pragma: no cover
            raise OperationNotSupported(f, 'resultant')

        return per(result, remove=0)

    def discriminant(f):
        """Computes discriminant of `f`. """
        try:
            result = f.rep.discriminant()
        except AttributeError: # pragma: no cover
            raise OperationNotSupported(f, 'discriminant')

        return f.per(result, remove=0)

    def cofactors(f, g):
        """Returns GCD of `f` and `g` and their cofactors. """
        _, per, F, G = f.unify(g)

        try:
            h, cff, cfg = F.cofactors(G)
        except AttributeError: # pragma: no cover
            raise OperationNotSupported(f, 'cofactors')

        return per(h), per(cff), per(cfg)

    def gcd(f, g):
        """Returns polynomial GCD of `f` and `g`. """
        _, per, F, G = f.unify(g)

        try:
            result = F.gcd(G)
        except AttributeError: # pragma: no cover
            raise OperationNotSupported(f, 'gcd')

        return per(result)

    def lcm(f, g):
        """Returns polynomial LCM of `f` and `g`. """
        _, per, F, G = f.unify(g)

        try:
            result = F.lcm(G)
        except AttributeError: # pragma: no cover
            raise OperationNotSupported(f, 'lcm')

        return per(result)

    def trunc(f, p):
        """Reduce `f` modulo a constant `p`. """
        p = f.rep.dom.convert(p)

        try:
            result = f.rep.trunc(p)
        except AttributeError: # pragma: no cover
            raise OperationNotSupported(f, 'trunc')

        return f.per(result)

    def monic(f):
        """Divides all coefficients by `LC(f)`. """
        try:
            result = f.rep.monic()
        except AttributeError: # pragma: no cover
            raise OperationNotSupported(f, 'monic')

        return f.per(result)

    def content(f):
        """Returns GCD of polynomial coefficients. """
        try:
            result = f.rep.content()
        except AttributeError: # pragma: no cover
            raise OperationNotSupported(f, 'content')

        return f.rep.dom.to_sympy(result)

    def primitive(f):
        """Returns content and a primitive form of `f`. """
        try:
            cont, result = f.rep.primitive()
        except AttributeError: # pragma: no cover
            raise OperationNotSupported(f, 'primitive')

        return f.rep.dom.to_sympy(cont), f.per(result)

    def compose(f, g):
        """Computes functional composition of `f` and `g`. """
        _, per, F, G = f.unify(g)

        try:
            result = F.compose(G)
        except AttributeError: # pragma: no cover
            raise OperationNotSupported(f, 'compose')

        return per(result)

    def decompose(f):
        """Computes functional decomposition of `f`. """
        try:
            result = f.rep.decompose()
        except AttributeError: # pragma: no cover
            raise OperationNotSupported(f, 'decompose')

        return map(f.per, result)

    def sturm(f, **args):
        """Computes the Sturm sequence of `f`. """
        if args.get('auto', True):
            f = f.to_field()

        try:
            result = f.rep.sturm()
        except AttributeError: # pragma: no cover
            raise OperationNotSupported(f, 'sturm')

        return map(f.per, result)

    def sqf_norm(f):
        """Computes square-free norm of `f`. """
        try:
            s, g, r = f.rep.sqf_norm()
        except AttributeError: # pragma: no cover
            raise OperationNotSupported(f, 'sqf_norm')

        return s, f.per(g), f.per(r)

    def sqf_part(f):
        """Computes square-free part of `f`. """
        try:
            result = f.rep.sqf_part()
        except AttributeError: # pragma: no cover
            raise OperationNotSupported(f, 'sqf_part')

        return f.per(result)

    def _perify_factors(f, factors):
        """Apply `per` functions to `(f_i, k)` factors. """
        if type(factors) is tuple:
            return f.rep.dom.to_sympy(factors[0]), \
                [ (f.per(g), k) for g, k in factors[1] ]
        else:
            return [ (f.per(g), k) for g, k in factors ]

    def sqf_list(f, **args):
        """Returns a list of square-free factors of `f`. """
        try:
            result = f.rep.sqf_list(**args)
        except AttributeError: # pragma: no cover
            raise OperationNotSupported(f, 'sqf_list')

        return f._perify_factors(result)

    def factor_list(f, **args):
        """Returns a list of irreducible factors of `f`. """
        try:
            result = f.rep.factor_list(**args)
        except DomainError:
            return S.One, [(f, 1)]
        except AttributeError: # pragma: no cover
            raise OperationNotSupported(f, 'factor_list')

        return f._perify_factors(result)

    def intervals(f, **args):
        """Compute isolating intervals for roots of `f`. """
        dom, eps = f.rep.dom.get_field(), args.get('eps')

        if eps is not None:
            args['eps'] = dom.convert(eps)

        try:
            result = f.rep.intervals(**args)
        except AttributeError: # pragma: no cover
            raise OperationNotSupported(f, 'intervals')

        if not args.get('sqf'):
            return [ ((dom.to_sympy(s), dom.to_sympy(t)), k) for ((s, t), k) in result ]
        else:
            return [ (dom.to_sympy(s), dom.to_sympy(t)) for (s, t) in result ]

    def nroots(f, **args):
        """Compute numerical approximations of roots of `f`. """
        if f.is_multivariate:
            raise PolynomialError("can't compute roots of a multivariate polynomial")

        try:
            coeffs = [ complex(c) for c in f.all_coeffs() ]
        except ValueError:
            raise DomainError("numerical domain expected, got %s" % f.rep.dom)

        return sympify(npolyroots(coeffs, **args))

    def cancel(f, g):
        """Cancel common factors in a rational function `f/g`.  """
        dom, per, F, G = f.unify(g)

        if F.is_zero or G.is_zero:
            return S.One, per(F), per(G)

        if dom.has_Field and dom.has_assoc_Ring:
            cF, F = F.ground_to_ring()
            cG, G = G.ground_to_ring()

            F = F.to_ring()
            G = G.to_ring()

        try:
            _, P, Q = F.cofactors(G)
        except AttributeError: # pragma: no cover
            raise OperationNotSupported(f, 'cofactors')

        if dom.has_Field and dom.has_assoc_Ring:
            P, Q = P.to_field(), Q.to_field()

            cF = dom.to_sympy(cF)
            cG = dom.to_sympy(cG)

            coeff = cG/cF
        else:
            coeff = S.One

        return coeff, per(P), per(Q)

    @property
    def is_zero(f):
        """Returns `True` if `f` is a zero polynomial. """
        return f.rep.is_zero

    @property
    def is_one(f):
        """Returns `True` if `f` is a unit polynomial. """
        return f.rep.is_one

    @property
    def is_sqf(f):
        """Returns `True` if `f` is a square-free polynomial. """
        return f.rep.is_sqf

    @property
    def is_monic(f):
        """Returns `True` if the leading coefficient of `f` is one. """
        return f.rep.is_monic

    @property
    def is_primitive(f):
        """Returns `True` if GCD of coefficients of `f` is one. """
        return f.rep.is_primitive

    @property
    def is_ground(f):
        """Returns `True` if `f` is an element of the ground domain. """
        return f.rep.is_ground

    @property
    def is_linear(f):
        """Returns `True` if `f` is linear in all its variables. """
        return f.rep.is_linear

    @property
    def is_monomial(f):
        """Returns `True` if `f` is zero or has only one term. """
        return f.length() <= 1

    @property
    def is_homogeneous(f):
        """Returns `True` if `f` has zero trailing coefficient. """
        return f.rep.is_homogeneous

    @property
    def is_irreducible(f):
        """Returns `True` if `f` has no factors over its domain. """
        return f.rep.is_irreducible

    @property
    def is_univariate(f):
        """Returns `True` if `f` is an univariate polynomial. """
        return len(f.gens) == 1

    @property
    def is_multivariate(f):
        """Returns `True` if `f` is a multivariate polynomial. """
        return len(f.gens) != 1

    def __abs__(f):
        return f.abs()

    def __neg__(f):
        return f.neg()

    @_sympifyit('g', NotImplemented)
    def __add__(f, g):
        if not g.is_Poly:
            try:
                g = Poly(g, *f.gens)
            except PolynomialError:
                return f.as_basic() + g

        return f.add(g)

    @_sympifyit('g', NotImplemented)
    def __radd__(f, g): # pragma: no cover
        if not g.is_Poly:
            try:
                g = Poly(g, *f.gens)
            except PolynomialError:
                return g + f.as_basic()

        return g.add(f)

    @_sympifyit('g', NotImplemented)
    def __sub__(f, g):
        if not g.is_Poly:
            try:
                g = Poly(g, *f.gens)
            except PolynomialError:
                return f.as_basic() - g

        return f.sub(g)

    @_sympifyit('g', NotImplemented)
    def __rsub__(f, g): # pragma: no cover
        if not g.is_Poly:
            try:
                g = Poly(g, *f.gens)
            except PolynomialError:
                return g - f.as_basic()

        return g.sub(f)

    @_sympifyit('g', NotImplemented)
    def __mul__(f, g):
        if not g.is_Poly:
            try:
                g = Poly(g, *f.gens)
            except PolynomialError:
                return f.as_basic()*g

        return f.mul(g)

    @_sympifyit('g', NotImplemented)
    def __rmul__(f, g): # pragma: no cover
        if not g.is_Poly:
            try:
                g = Poly(g, *f.gens)
            except PolynomialError:
                return g*f.as_basic()

        return g.mul(f)

    @_sympifyit('n', NotImplemented)
    def __pow__(f, n):
        if n.is_Integer and n >= 0:
            return f.pow(n)
        else:
            return f.as_basic()**n

    @_sympifyit('g', NotImplemented)
    def __divmod__(f, g):
        if not g.is_Poly:
            g = Poly(g, *f.gens)

        return f.div(g)

    @_sympifyit('g', NotImplemented)
    def __rdivmod__(f, g): # pragma: no cover
        if not g.is_Poly:
            g = Poly(g, *f.gens)

        return g.div(f)

    @_sympifyit('g', NotImplemented)
    def __mod__(f, g):
        if not g.is_Poly:
            g = Poly(g, *f.gens)

        return f.rem(g)

    @_sympifyit('g', NotImplemented)
    def __rmod__(f, g): # pragma: no cover
        if not g.is_Poly:
            g = Poly(g, *f.gens)

        return g.rem(f)

    @_sympifyit('g', NotImplemented)
    def __floordiv__(f, g):
        if not g.is_Poly:
            g = Poly(g, *f.gens)

        return f.exquo(g)

    @_sympifyit('g', NotImplemented)
    def __rfloordiv__(f, g): # pragma: no cover
        if not g.is_Poly:
            g = Poly(g, *f.gens)

        return g.exquo(f)

    @_sympifyit('g', NotImplemented)
    def __eq__(f, g):
        if not g.is_Poly:
            try:
                g = Poly(g, *f.gens, **{'domain': f.get_domain()})
            except (PolynomialError, DomainError, CoercionFailed):
                return False

        return f.rep == g.rep and f.gens == g.gens

    @_sympifyit('g', NotImplemented)
    def __ne__(f, g):
        return not f.__eq__(g)

    def __nonzero__(f):
        return not f.is_zero

def NonStrictPoly(f, *gens, **args):
    """Create a Poly instance with `strict` keyword set.  """
    args = dict(args)
    args['strict'] = False
    return Poly(f, *gens, **args)

def _polify_basic(f, g, *gens, **args):
    """Cooperatively make polynomials out of `f` and `g`. """
    if gens:
        F = NonStrictPoly(f, *gens, **args)
        G = NonStrictPoly(g, *gens, **args)

        if not F.is_Poly or not G.is_Poly:
            raise CoercionFailed(F, G) # pragma: no cover
        else:
            return F, G
    else:
        F = NonStrictPoly(f, **args)
        G = NonStrictPoly(g, **args)

        if F.is_Poly:
            if G.is_Poly:
                return F, G
            else:
                return F, Poly(g, *F.gens, **args)
        else:
            if G.is_Poly:
                return Poly(f, *G.gens, **args), G
            else:
                raise CoercionFailed(F, G)

def _update_args(args, key, value):
    """Add a new `(key, value)` pair to arguments dict. """
    args = dict(args)

    if not args.has_key(key):
        args[key] = value

    return args

def _basify_factors(factors):
    """Convert `(f_i, k)` factors to Basic expressions. """
    if type(factors) is tuple:
        return factors[0], [ (g.as_basic(), k) for g, k in factors[1] ]
    else:
        return [ (g.as_basic(), k) for g, k in factors ]

def _should_return_basic(*polys, **args):
    """Figure out if results should be returned as basic. """
    query = args.get('polys')

    if query is not None:
        return not query
    else:
        return not all(isinstance(poly, Poly) for poly in polys)

def degree(f, *gens, **args):
    """Returns degree of `f` in the given generator. """
    try:
        F = Poly(f, *_analyze_gens(gens), **args)
    except GeneratorsNeeded:
        raise GeneratorsNeeded("can't compute degree of %s without generators" % f)

    degree = F.degree(args.get('gen', 0))

    return Integer(degree)

def degree_list(f, *gens, **args):
    """Returns a list of degrees of `f` in all generators. """
    try:
        F = Poly(f, *_analyze_gens(gens), **args)
    except GeneratorsNeeded:
        raise GeneratorsNeeded("can't compute degrees list of %s without generators" % f)

    degrees = F.degree_list()

    return tuple(map(Integer, degrees))

def pdiv(f, g, *gens, **args):
    """Polynomial pseudo-division of `f` and `g`. """
    gens = _analyze_gens(gens)

    try:
        F, G = _polify_basic(f, g, *gens, **args)
    except CoercionFailed, (f, g):
        raise GeneratorsNeeded("can't compute pseudo division of %s and %s without generators" % (f, g))

    q, r = F.pdiv(G)

    if _should_return_basic(f, g, **args):
        return q.as_basic(), r.as_basic()
    else:
        return q, r

def prem(f, g, *gens, **args):
    """Polynomial pseudo-remainder of `f` and `g`. """
    gens = _analyze_gens(gens)

    try:
        F, G = _polify_basic(f, g, *gens, **args)
    except CoercionFailed, (f, g):
        raise GeneratorsNeeded("can't compute pseudo remainder of %s and %s without generators" % (f, g))

    r = F.prem(G)

    if _should_return_basic(f, g, **args):
        return r.as_basic()
    else:
        return r

def pquo(f, g, *gens, **args):
    """Polynomial pseudo-quotient of `f` and `g`. """
    gens = _analyze_gens(gens)

    try:
        F, G = _polify_basic(f, g, *gens, **args)
    except CoercionFailed, (f, g):
        raise GeneratorsNeeded("can't compute pseudo quotient of %s and %s without generators" % (f, g))

    q = F.pquo(G)

    if _should_return_basic(f, g, **args):
        return q.as_basic()
    else:
        return q

def pexquo(f, g, *gens, **args):
    """Polynomial exact pseudo-quotient of `f` and `g`. """
    gens = _analyze_gens(gens)

    try:
        F, G = _polify_basic(f, g, *gens, **args)
    except CoercionFailed, (f, g):
        raise GeneratorsNeeded("can't compute pseudo quotient of %s and %s without generators" % (f, g))

    q = F.pexquo(G)

    if _should_return_basic(f, g, **args):
        return q.as_basic()
    else:
        return q

def div(f, g, *gens, **args):
    """Polynomial division with remainder of `f` and `g`. """
    gens = _analyze_gens(gens)

    try:
        F, G = _polify_basic(f, g, *gens, **args)
    except CoercionFailed, (f, g):
        raise GeneratorsNeeded("can't compute division of %s and %s without generators" % (f, g))

    q, r = F.div(G)

    if _should_return_basic(f, g, **args):
        return q.as_basic(), r.as_basic()
    else:
        return q, r

def rem(f, g, *gens, **args):
    """Computes polynomial remainder of `f` and `g`. """
    gens = _analyze_gens(gens)

    try:
        F, G = _polify_basic(f, g, *gens, **args)
    except CoercionFailed, (f, g):
        raise GeneratorsNeeded("can't compute remainder of %s and %s without generators" % (f, g))

    r = F.rem(G)

    if _should_return_basic(f, g, **args):
        return r.as_basic()
    else:
        return r

def quo(f, g, *gens, **args):
    """Computes polynomial quotient of `f` and `g`. """
    gens = _analyze_gens(gens)

    try:
        F, G = _polify_basic(f, g, *gens, **args)
    except CoercionFailed, (f, g):
        raise GeneratorsNeeded("can't compute quotient of %s and %s without generators" % (f, g))

    q = F.quo(G)

    if _should_return_basic(f, g, **args):
        return q.as_basic()
    else:
        return q

def exquo(f, g, *gens, **args):
    """Computes polynomial exact quotient of `f` and `g`. """
    gens = _analyze_gens(gens)

    try:
        F, G = _polify_basic(f, g, *gens, **args)
    except CoercionFailed, (f, g):
        raise GeneratorsNeeded("can't compute quotient of %s and %s without generators" % (f, g))

    q = F.exquo(G)

    if _should_return_basic(f, g, **args):
        return q.as_basic()
    else:
        return q

def half_gcdex(f, g, *gens, **args):
    """Half extended Euclidean algorithm of `f` and `g`. """
    args = _update_args(args, 'field', True)
    gens = _analyze_gens(gens)

    try:
        F, G = _polify_basic(f, g, *gens, **args)
    except CoercionFailed, (f, g):
        try:
            return f.half_gcdex(g)
        except (AttributeError, TypeError): # pragma: no cover
            raise GeneratorsNeeded("can't compute half extended GCD of %s and %s without generators" % (f, g))

    s, h = F.half_gcdex(G, **args)

    if _should_return_basic(f, g, **args):
        return s.as_basic(), h.as_basic()
    else:
        return s, h

def gcdex(f, g, *gens, **args):
    """Extended Euclidean algorithm of `f` and `g`. """
    args = _update_args(args, 'field', True)
    gens = _analyze_gens(gens)

    try:
        F, G = _polify_basic(f, g, *gens, **args)
    except CoercionFailed, (f, g):
        try:
            return f.gcdex(g)
        except (AttributeError, TypeError): # pragma: no cover
            raise GeneratorsNeeded("can't compute extended GCD of %s and %s without generators" % (f, g))

    s, t, h = F.gcdex(G, **args)

    if _should_return_basic(f, g, **args):
        return s.as_basic(), t.as_basic(), h.as_basic()
    else:
        return s, t, h

def invert(f, g, *gens, **args):
    """Invert `f` modulo `g`, if possible. """
    args = _update_args(args, 'field', True)
    gens = _analyze_gens(gens)

    try:
        F, G = _polify_basic(f, g, *gens, **args)
    except CoercionFailed, (f, g):
        try:
            return f.invert(g)
        except (AttributeError, TypeError): # pragma: no cover
            raise GeneratorsNeeded("can't compute inversion of %s modulo %s without generators" % (f, g))

    h = F.invert(G, **args)

    if _should_return_basic(f, g, **args):
        return h.as_basic()
    else:
        return h

def subresultants(f, g, *gens, **args):
    """Computes subresultant PRS sequence of `f` and `g`. """
    gens = _analyze_gens(gens)

    try:
        F, G = _polify_basic(f, g, *gens, **args)
    except CoercionFailed, (f, g):
        raise GeneratorsNeeded("can't compute subresultants of %s and %s without generators" % (f, g))

    result = F.subresultants(G)

    if _should_return_basic(f, g, **args):
        return [ r.as_basic() for r in result ]
    else:
        return result

def resultant(f, g, *gens, **args):
    """Computes resultant of `f` and `g` via PRS. """
    gens = _analyze_gens(gens)

    try:
        F, G = _polify_basic(f, g, *gens, **args)
    except CoercionFailed, (f, g):
        raise GeneratorsNeeded("can't compute resultant of %s and %s without generators" % (f, g))

    result = F.resultant(G)

    if _should_return_basic(f, g, **args):
        return result.as_basic()
    else:
        return result

def discriminant(f, *gens, **args):
    """Computes discriminant of `f`. """
    F = NonStrictPoly(f, *_analyze_gens(gens), **args)

    if not F.is_Poly:
        raise GeneratorsNeeded("can't compute discriminant of %s without generators" % f)

    result = F.discriminant()

    if _should_return_basic(f, **args):
        return result.as_basic()
    else:
        return result

def cofactors(f, g, *gens, **args):
    """Returns GCD of `f` and `g` and their cofactors. """
    gens = _analyze_gens(gens)

    try:
        F, G = _polify_basic(f, g, *gens, **args)
    except CoercionFailed, (f, g):
        try:
            return f.cofactors(g)
        except (AttributeError, TypeError): # pragma: no cover
            raise GeneratorsNeeded("can't compute cofactors of %s and %s without generators" % (f, g))

    h, cff, cfg = F.cofactors(G)

    if _should_return_basic(f, g, **args):
        return h.as_basic(), cff.as_basic(), cfg.as_basic()
    else:
        return h, cff, cfg

def gcd(f, g, *gens, **args):
    """Returns polynomial GCD of `f` and `g`. """
    gens = _analyze_gens(gens)

    try:
        F, G = _polify_basic(f, g, *gens, **args)
    except CoercionFailed, (f, g):
        try:
            return f.gcd(g)
        except (AttributeError, TypeError): # pragma: no cover
            raise GeneratorsNeeded("can't compute GCD of %s and %s without generators" % (f, g))

    result = F.gcd(G)

    if _should_return_basic(f, g, **args):
        return result.as_basic()
    else:
        return result

def lcm(f, g, *gens, **args):
    """Returns polynomial LCM of `f` and `g`. """
    gens = _analyze_gens(gens)

    try:
        F, G = _polify_basic(f, g, *gens, **args)
    except CoercionFailed, (f, g):
        try:
            return f.lcm(g)
        except (AttributeError, TypeError): # pragma: no cover
            raise GeneratorsNeeded("can't compute LCM of %s and %s without generators" % (f, g))

    result = F.lcm(G)

    if _should_return_basic(f, g, **args):
        return result.as_basic()
    else:
        return result

def terms_gcd(f, *gens, **args):
    """Remove GCD of terms from the polynomial `f`. """
    F = NonStrictPoly(f, *_analyze_gens(gens), **args)

    if not F.is_Poly:
        return f

    J, result = F.terms_gcd()
    dom = result.get_domain()

    if dom.has_Field or not dom.is_Exact:
        C, result = result.LC(), result.monic()
    else:
        C, result = result.primitive()

    return C * Mul(*[ x**j for x, j in zip(F.gens, J) ]) * result.as_basic()

def trunc(f, p, *gens, **args):
    """Reduce `f` modulo a constant `p`. """
    F = NonStrictPoly(f, *_analyze_gens(gens), **args)

    if not F.is_Poly:
        return F % p

    if _should_return_basic(f, **args):
        return F.trunc(p).as_basic()
    else:
        return F.trunc(p)

def monic(f, *gens, **args):
    """Divides all coefficients by `LC(f)`. """
    args = _update_args(args, 'field', True)
    F = NonStrictPoly(f, *_analyze_gens(gens), **args)

    if not F.is_Poly:
        raise GeneratorsNeeded("can't compute monic polynomial of %s without generators" % f)

    if _should_return_basic(f, **args):
        return F.monic().as_basic()
    else:
        return F.monic()

def content(f, *gens, **args):
    """Returns GCD of polynomial coefficients. """
    F = NonStrictPoly(f, *_analyze_gens(gens), **args)

    if not F.is_Poly:
        raise GeneratorsNeeded("can't compute content of %s without generators" % f)
    else:
        return F.content()

def primitive(f, *gens, **args):
    """Returns content and a primitive form of `f`. """
    F = NonStrictPoly(f, *_analyze_gens(gens), **args)

    if not F.is_Poly:
        raise GeneratorsNeeded("can't compute primitive part of %s without generators" % f)

    cont, result = F.primitive()

    if _should_return_basic(f, **args):
        return cont, result.as_basic()
    else:
        return cont, result

def compose(f, g, *gens, **args):
    """Returns functional composition `f(g)`. """
    gens = _analyze_gens(gens)

    try:
        F, G = _polify_basic(f, g, *gens, **args)
    except CoercionFailed, (f, g):
        raise GeneratorsNeeded("can't compute composition of %s and %s without generators" % (f, g))

    result = F.compose(G)

    if _should_return_basic(f, g, **args):
        return result.as_basic()
    else:
        return result

def decompose(f, *gens, **args):
    """Computes functional decomposition of `f`. """
    F = NonStrictPoly(f, *_analyze_gens(gens), **args)

    if not F.is_Poly:
        raise GeneratorsNeeded("can't compute functional decomposition of %s without generators" % f)

    result = F.decompose()

    if _should_return_basic(f, **args):
        return [ r.as_basic() for r in result ]
    else:
        return result

def sturm(f, *gens, **args):
    """Computes the Sturm sequence of `f`. """
    args = _update_args(args, 'field', True)
    F = NonStrictPoly(f, *_analyze_gens(gens), **args)

    if not F.is_Poly:
        raise GeneratorsNeeded("can't compute Sturm sequence of %s without generators" % f)

    result = F.sturm()

    if _should_return_basic(f, **args):
        return [ r.as_basic() for r in result ]
    else:
        return result

def sqf_norm(f, *gens, **args):
    """Computes square-free norm of `f`. """
    F = NonStrictPoly(f, *_analyze_gens(gens), **args)

    if not F.is_Poly:
        raise GeneratorsNeeded("can't compute square-free norm of %s without generators" % f)

    s, g, r = F.sqf_norm()

    if _should_return_basic(f, **args):
        return Integer(s), g.as_basic(), r.as_basic()
    else:
        return Integer(s), g, r

def sqf_part(f, *gens, **args):
    """Computes square-free part of `f`. """
    F = NonStrictPoly(f, *_analyze_gens(gens), **args)

    if not F.is_Poly:
        raise GeneratorsNeeded("can't compute square-free part of %s without generators" % f)

    result = F.sqf_part()

    if _should_return_basic(f, **args):
        return result.as_basic()
    else:
        return result

def sqf_list(f, *gens, **args):
    """Returns a list of square-free factors of `f`. """
    F = NonStrictPoly(f, *_analyze_gens(gens), **args)

    if not F.is_Poly:
        raise GeneratorsNeeded("can't compute square-free decomposition of %s without generators" % f)

    result = F.sqf_list(**args)

    if _should_return_basic(f, **args):
        return _basify_factors(result)
    else:
        return result

def sqf(f, *gens, **args):
    """Returns square-free decomposition of `f`. """
    frac = args.get('frac', False)
    gens = _analyze_gens(gens)

    def _sqf(f):
        """Squaqre-free factor a true polynomial expression. """
        F = NonStrictPoly(f, *gens, **args)

        if not F.is_Poly:
            return (S.One, F)

        (coeff, factors), result = F.sqf_list(**args), S.One

        for g, k in factors:
            result *= g.as_basic()**k

        return (coeff, result)

    if not frac:
        coeff, factors = _sqf(f)
    else:
        p, q = cancel(f).as_numer_denom()

        coeff_p, factors_p = _sqf(p)
        coeff_q, factors_q = _sqf(q)

        coeff = coeff_p / coeff_q
        factors = factors_p / factors_q

    if coeff == 1:
        return factors
    elif coeff == -1:
        return -factors
    elif not factors.is_Add:
        return coeff*factors
    else:
        return Mul(coeff, factors, evaluate=False)

def factor_list(f, *gens, **args):
    """Returns a list of irreducible factors of `f`. """
    F = NonStrictPoly(f, *_analyze_gens(gens), **args)

    if not F.is_Poly:
        raise GeneratorsNeeded("can't compute factorization of %s without generators" % f)

    result = F.factor_list(**args)

    if _should_return_basic(f, **args):
        return _basify_factors(result)
    else:
        return result

def factor(f, *gens, **args):
    """Returns factorization into irreducibles of `f`. """
    frac = args.get('frac', False)
    gens = _analyze_gens(gens)

    def _factor(f):
        """Factor a true polynomial expression. """
        F = NonStrictPoly(f, *gens, **args)

        if not F.is_Poly:
            return (S.One, F)

        (coeff, factors), result = F.factor_list(**args), S.One

        for g, k in factors:
            result *= g.as_basic()**k

        return (coeff, result)

    if not frac:
        coeff, factors = _factor(f)
    else:
        p, q = cancel(f).as_numer_denom()

        coeff_p, factors_p = _factor(p)
        coeff_q, factors_q = _factor(q)

        coeff = coeff_p / coeff_q
        factors = factors_p / factors_q

    if coeff == 1:
        return factors
    elif coeff == -1:
        return -factors
    elif not factors.is_Add:
        return coeff*factors
    else:
        return Mul(coeff, factors, evaluate=False)

def intervals(f, *gens, **args):
    """Compute isolating intervals for roots of `f`. """
    F = NonStrictPoly(f, *_analyze_gens(gens), **args)

    if F.is_Poly:
        return F.intervals(**args)
    else:
        raise GeneratorsNeeded("can't isolate roots of %s without generators" % f)

def nroots(f, *gens, **args):
    """Compute numerical approximations of roots of `f`. """
    F = NonStrictPoly(f, *_analyze_gens(gens), **args)

    if F.is_Poly:
        return F.nroots(**args)
    else:
        raise GeneratorsNeeded("can't approximate roots of %s without generators" % f)

def cancel(f, *gens, **args):
    """Cancel common factors in a rational function `f`.  """
    f = sympify(f)

    if type(f) is not tuple:
        if f.is_Number:
            return f
        else:
            p, q = f.as_numer_denom()
    else:
        p, q = f

    gens = _analyze_gens(gens)

    try:
        F, G = _polify_basic(p, q, *gens, **args)
    except CoercionFailed:
        if type(f) is not tuple:
            return f
        else:
            return S.One, p, q

    c, P, Q = F.cancel(G)

    if type(f) is not tuple:
        return c*(P.as_basic()/Q.as_basic())
    else:
        if _should_return_basic(p, q, **args):
            return c, P.as_basic(), Q.as_basic()
        else:
            return c, P, Q

def reduced(f, G, *gens, **args):
    """Reduces a polynomial `f` modulo a set of polynomials `G`. """
    if 'modulus' in args:
        raise PolynomialError("can't reduce a polynomial over a finite field")

    H = [f] + list(G)

    order = Poly._analyze_order({'order': args.pop('order', 'lex')})
    basic = _should_return_basic(*H, **args)

    gens = _analyze_gens(gens)

    H = [ Poly(h, *gens, **args) for h in H ]
    dom, gens = H[0].get_domain(), H[0].gens

    for h in H[1:]:
        gens = _unify_gens(gens, h.gens)
        dom = dom.unify(h.get_domain(), gens)

    lev = len(gens) - 1

    for i, h in enumerate(H):
        h = Poly(h, *gens, **{'domain': dom})
        H[i] = sdp_from_dict(h.rep.to_dict(), order)

    Q, r = sdp_div(H[0], H[1:], lev, order, dom)

    Q = [ Poly(DMP(dict(q), dom, lev), *gens) for q in Q ]
    r =   Poly(DMP(dict(r), dom, lev), *gens)

    if basic:
        return [ q.as_basic() for q in Q ], r.as_basic()
    else:
        return Q, r

def groebner(F, *gens, **args):
    """Computes reduced Groebner basis for a set of polynomials. """
    if 'modulus' in args:
        raise PolynomialError("can't compute Groebner basis over a finite field")

    order = Poly._analyze_order({'order': args.pop('order', 'lex')})
    basic = _should_return_basic(*F, **args)

    args = _update_args(args, 'field', True)
    gens = _analyze_gens(gens)

    if not F:
        return []

    F = [ Poly(f, *gens, **args) for f in F ]
    dom, gens = F[0].get_domain(), F[0].gens

    for f in F[1:]:
        gens = _unify_gens(gens, f.gens)
        dom = dom.unify(f.get_domain(), gens)

    lev = len(gens) - 1

    for i, f in enumerate(F):
        f = Poly(f, *gens, **{'domain': dom})
        F[i] = sdp_from_dict(f.rep.to_dict(), order)

    G = sdp_groebner(F, lev, order, dom)

    G = [ Poly(DMP(dict(g), dom, lev), *gens) for g in G ]

    if basic:
        return [ g.as_basic() for g in G ]
    else:
        return G

def symmetrize(f, *gens, **args):
    """Rewrite a polynomial in terms of elementary symmetric polynomials. """
    try:
        f = Poly(f, *_analyze_gens(gens), **args)
    except GeneratorsNeeded:
        if args.get('formal', False):
            return (f, S.Zero, {})
        else:
            return (f, S.Zero)

    from sympy.polys.specialpolys import symmetric_poly

    polys, symbols = [], numbered_symbols('s', start=1)

    gens, dom = f.gens, f.get_domain()

    for i in range(0, len(f.gens)):
        poly = symmetric_poly(i+1, gens, polys=True)
        polys.append((symbols.next(), poly.set_domain(dom)))

    indices = range(0, len(gens) - 1)
    weights = range(len(gens), 0, -1)

    symmetric = []

    if not f.is_homogeneous:
        symmetric.append(f.TC())
        f -= f.TC()

    while f:
        _height, _monom, _coeff = -1, None, None

        for i, (monom, coeff) in enumerate(f.terms()):
            if all(monom[i] >= monom[i+1] for i in indices):
                height = max([ n*m for n, m in zip(weights, monom) ])

                if height > _height:
                    _height, _monom, _coeff = height, monom, coeff

        if _height != -1:
            monom, coeff = _monom, _coeff
        else:
            break

        exponents = []

        for m1, m2 in zip(monom, monom[1:] + (0,)):
            exponents.append(m1 - m2)

        term = [ s**n for (s, _), n in zip(polys, exponents) ]
        poly = [ p**n for (_, p), n in zip(polys, exponents) ]

        symmetric.append(Mul(coeff, *term))

        product = poly[0].mul(coeff)

        for p in poly[1:]:
            product = product.mul(p)

        f -= product

    polys = [ (s, p.as_basic()) for s, p in polys ]

    if args.get('formal', False):
        return (Add(*symmetric), f.as_basic(), dict(polys))
    else:
        return (Add(*symmetric).subs(polys), f.as_basic())

def horner(f, *gens, **args):
    """Apply Horner's rule to put a polynomial in Horner form. """
    F = NonStrictPoly(f, *_analyze_gens(gens), **args)

    if not F.is_Poly:
        return F

    form, gen = S.Zero, F.gen

    if F.is_univariate:
        for coeff in F.all_coeffs():
            form = form*gen + coeff
    else:
        F, gens = Poly(F, gen), gens[1:]

        for coeff in F.all_coeffs():
            form = form*gen + horner(coeff, *gens, **args)

    return form

def poly(expr, **args):
    """Efficiently transform an expression into a polynomial. """
    expr = sympify(expr)

    if expr.is_Poly:
        return expr.reorder(**args)

    terms, poly_terms = [], []

    for term in expr.as_Add():
        factors, poly_factors = [], []

        for factor in term.as_Mul():
            if factor.is_Add:
                poly_factors.append(poly(factor))
            elif factor.is_Pow and factor.base.is_Add and factor.exp.is_Integer:
                poly_factors.append(poly(factor.base).pow(factor.exp))
            else:
                factors.append(factor)

        if not poly_factors:
            terms.append(term)
        else:
            product = poly_factors[0]

            for factor in poly_factors[1:]:
                product = product.mul(factor)

            if factors:
                factor = Mul(*factors)

                if factor.is_Number:
                    product = product.mul(factor)
                else:
                    product = product.mul(Poly(factor, expand=False))

            poly_terms.append(product)

    if not poly_terms:
        result = Poly(expr, expand=False)
    else:
        result = poly_terms[0]

        for term in poly_terms[1:]:
            result = result.add(term)

        if terms:
            term = Add(*terms)

            if term.is_Number:
                result = result.add(term)
            else:
                result = result.add(Poly(term, expand=False))

    return result.reorder(**args)

