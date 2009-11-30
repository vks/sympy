from basic import Basic, NoUnionError
from sympify import _sympify

def Rel(a, b, op):
    """
    A handy wrapper around the Relational class.
    Rel(a,b, op)

    Example:
    >>> from sympy import Rel
    >>> from sympy.abc import x, y
    >>> Rel(y, x+x**2, '==')
    y == x + x**2

    """
    return Relational(a,b,op)

def Eq(a, b=0):
    """
    A handy wrapper around the Relational class.
    Eq(a,b)

    Example:
    >>> from sympy import Eq
    >>> from sympy.abc import x, y
    >>> Eq(y, x+x**2)
    y == x + x**2

    """
    return Relational(a,b,'==')

def Ne(a, b):
    """
    A handy wrapper around the Relational class.
    Ne(a,b)

    Example:
    >>> from sympy import Ne
    >>> from sympy.abc import x, y
    >>> Ne(y, x+x**2)
    y != x + x**2

    """
    return Relational(a,b,'!=')

def Lt(a, b):
    """
    A handy wrapper around the Relational class.
    Lt(a,b)

    Example:
    >>> from sympy import Lt
    >>> from sympy.abc import x, y
    >>> Lt(y, x+x**2)
    y < x + x**2

    """
    return Relational(a,b,'<')

def Le(a, b):
    """
    A handy wrapper around the Relational class.
    Le(a,b)

    Example:
    >>> from sympy import Le
    >>> from sympy.abc import x, y
    >>> Le(y, x+x**2)
    y <= x + x**2

    """
    return Relational(a,b,'<=')

def Gt(a, b):
    """
    A handy wrapper around the Relational class.
    Gt(a,b)

    Example:
    >>> from sympy import Gt
    >>> from sympy.abc import x, y
    >>> Gt(y, x+x**2)
    x + x**2 < y

    """
    return Relational(a,b,'>')

def Ge(a, b):
    """
    A handy wrapper around the Relational class.
    Ge(a,b)

    Example:
    >>> from sympy import Ge
    >>> from sympy.abc import x, y
    >>> Ge(y, x+x**2)
    x + x**2 <= y

    """
    return Relational(a,b,'>=')

class Relational(Basic):

    __slots__ = []

    @staticmethod
    def get_relational_class(rop):
        if rop is None or rop in ['==','eq']: return Equality, False
        if rop in ['!=','<>','ne']: return Unequality, False
        if rop in ['<','lt']: return StrictInequality, False
        if rop in ['>','gt']: return StrictInequality, True
        if rop in ['<=','le']: return Inequality, False
        if rop in ['>=','ge']: return Inequality, True
        raise ValueError("Invalid relational operator symbol: %r" % (rop))

    def __new__(cls, lhs, rhs, rop=None, **assumptions):
        lhs = _sympify(lhs)
        rhs = _sympify(rhs)
        if cls is not Relational:
            rop_cls = cls
        else:
            rop_cls, swap = Relational.get_relational_class(rop)
            if swap: lhs, rhs = rhs, lhs
        obj = Basic.__new__(rop_cls, lhs, rhs, **assumptions)
        return obj

    @property
    def lhs(self):
        return self._args[0]

    @property
    def rhs(self):
        return self._args[1]

    def _eval_subs(self, old, new):
        return self.__class__(self.lhs._eval_subs(old, new), self.rhs._eval_subs(old, new))

    def _evals(self):
        if (self.rhs - self.lhs).is_positive:
            if self.__class__ in (Inequality, StrictInequality):
                return True
            else:
                return False
        if (self.lhs - self.rhs).is_positive:
            if self.__class__ in (Inequality, StrictInequality):
                return False
            else:
                return True
        if (self.rhs - self.lhs).is_zero:
            if self.__class__ in (Inequality, Equality):
                return True
            else:
                return False
        return None

    def doit(self):
        e = self._evals()
        if e is not None:
            return e
        return self._doit()

    def complement(self):
        negatives = {
            Equality: Unequality,
            Unequality: Equality,
            StrictInequality: Inequality,
            Inequality: StrictInequality }
        return negatives[self.__class__](self.args[1], self.args[0])

    def union(self,other):
        try:
            return self._union(other)
        except NoUnionError:
            return (self | other)
        return (self | other)

    def _intersection(self,other):
        if not isinstance(other, Relational):
            raise NoUnionError(
                "Relational can be intersected with Relational only")
        r = self.complement()._union(other.complement())
        if not isinstance(r, Relational):
            raise NoUnionError(
                "Relational can be intersected with Relational only")
        return r.complement()

class Equality(Relational):

    rel_op = '=='

    __slots__ = []

    def __nonzero__(self):
        return self.lhs.compare(self.rhs)==0

    def _doit(self, **hints):
        lhs,rhs = [ term.doit(**hints) for term in self.args ]
        if self.lhs.is_comparable and self.rhs.is_comparable:
            if self.lhs.is_Number and self.rhs.is_Number:
                return self.lhs == self.rhs
        return self.new(lhs, rhs)

    def _union(self, other):
        if not isinstance(other, Relational):
            raise NoUnionError(
                "Relational can be united with Relational only")
        if ((type(other) == Equality) and
           (((self.lhs == other.lhs) and (self.rhs == other.rhs)) or
           ((self.lhs == other.rhs) and (self.rhs == other.lhs)))):
            return self.new(self.lhs, self.rhs)
        if ((type(other) == Unequality) and
           (((self.lhs == other.lhs) and (self.rhs == other.rhs)) or
           ((self.lhs == other.rhs) and (self.rhs == other.lhs)))):
            return True
        if (((type(other) == Inequality) or (type(other) == StrictInequality)) and
           (((self.lhs == other.lhs) and (self.rhs == other.rhs)) or
           ((self.lhs == other.rhs) and (self.rhs == other.lhs)))):
            return Inequality.new(other.lhs, other.rhs)
        raise NoUnionError("no meaningful union")

class Unequality(Relational):

    rel_op = '!='

    __slots__ = []

    def __nonzero__(self):
        return self.lhs.compare(self.rhs)!=0

    def _doit(self,**hints):
        lhs,rhs = [ term.doit(**hints) for term in self.args ]
        if self.lhs.is_comparable and self.rhs.is_comparable:
            if self.lhs.is_Number and self.rhs.is_Number:
                return self.lhs != self.rhs
        return self.new(lhs,rhs)

    def _union(self,other):
        if not isinstance(other,Relational):
            raise NoUnionError, "Relational can be united with Relational only"
        if (((type(other) == Unequality) or (type(other) == StrictInequality)
             or (type(other) == Inequality)) and
           ((((self.lhs == other.lhs) and (self.rhs == other.rhs)) or
           ((self.lhs == other.rhs) and (self.rhs == other.lhs))))):
                    return self.new(self.lhs, self.rhs)
        return True

class StrictInequality(Relational):

    rel_op = '<'

    __slots__ = []

    def __nonzero__(self):
        if self.lhs.is_comparable and self.rhs.is_comparable:
            if self.lhs.is_Number and self.rhs.is_Number:
                return self.lhs < self.rhs
            return self.lhs.evalf()<self.rhs.evalf()
        return self.lhs.compare(self.rhs) == -1

    def _doit(self, **hints):
        lhs, rhs = [ term.doit(**hints) for term in self.args ]
        if self.lhs.is_comparable and self.rhs.is_comparable:
            if self.lhs.is_Number and self.rhs.is_Number:
                return self.lhs < self.rhs
            return self.lhs.evalf() < self.rhs.evalf()
        return self.new(lhs, rhs)

    def _union(self, other):
        if not isinstance(other, Relational):
            raise NoUnionError(
                "Relational can be united with Relational only")
        if (type(other) == StrictInequality) or (type(other) == Inequality):
            if (self.rhs == other.rhs):
                if self.lhs < other.lhs:
                    return self.new(self.lhs, self.rhs)
                elif self.lhs >= other.lhs:
                    # self.lhs == other.lhs and other is Inequality is handled here
                    return other.new(other.lhs, other.rhs)
            if (self.lhs == other.lhs):
                if self.rhs > other.rhs:
                    return self.new(self.lhs, self.rhs)
                elif self.rhs <= other.rhs:
                    # self.rhs == other.rhs and other is Inequality is handled here
                    return other.new(other.lhs, other.rhs)
            if ((self.lhs == other.rhs) and (self.rhs == other.lhs)):
                if type(other) == Inequality:
                    return True
                if type(other) == StrictInequality:
                    return Equality(self.lhs, self.rhs)

        if ((type(other) == Equality) and
           (((self.lhs == other.lhs) and (self.rhs == other.rhs)) or
           ((self.lhs == other.rhs) and (self.rhs == other.lhs)))):
            return Inequality(self.lhs,self.rhs)
        if ((type(other) == Unequality) and
           (((self.lhs == other.lhs) and (self.rhs == other.rhs)) or
           ((self.lhs == other.rhs) and (self.rhs == other.lhs)))):
            return Unequality(self.lhs,self.rhs)
        raise NoUnionError("no meaningful union")

class Inequality(Relational):

    rel_op = '<='

    __slots__ = []

    def __nonzero__(self):
        if self.lhs.is_comparable and self.rhs.is_comparable:
            if self.lhs.is_Number and self.rhs.is_Number:
                return self.lhs <= self.rhs
            return self.lhs.evalf() <= self.rhs.evalf()
        return self.lhs.compare(self.rhs) <= 0

    def _doit(self,**hints):
        lhs, rhs = [ term.doit(**hints) for term in self.args ]
        if self.lhs.is_comparable and self.rhs.is_comparable:
            if self.lhs.is_Number and self.rhs.is_Number:
                return self.lhs <= self.rhs
            return self.lhs.evalf() <= self.rhs.evalf()
        return self.new(lhs, rhs)


    def _union(self,other):
        """ Returns the union if it is simpler than the original expression
            raises NoUnionError else.
        """
        if not isinstance(other, Relational):
            raise NoUnionError(
                "Relational can be united with Relational only")
        a = self.lhs
        b = self.rhs
        c = other.lhs
        d = other.rhs
        if a == c:
            if (d - a).is_positive:
                return True
            elif (a == d):
                if other.new == Inequality:
                    return True
                elif b == d or b == c:
                    if self.new == Inequality:
                        return True
                    else:
                        return False
                elif (c - b).is_positive:
                    return False
                elif (b - c).is_positive or (b - d).is_positive:
                    return True
                return self.new(a, b)
            elif b == c:
                if self.new == Inequality:
                    return True
                elif b == d:
                    if ((self.new == Inequality) or
                        (other.__class__ == Inequality)):
                        return True
                    else:
                        return False
                elif (d -b).is_positive:
                    return False
                elif (b - d).is_positive:
                    return False
                return other.new(a, d)
            elif b == d:
                if self.new == other.__class__:
                    return self.new(a, d)
                return Inequality(a, d)
            elif (d - b).is_positive:
                return other.new(a,d)
            elif (b - d).is_positive:
                return self.new(a, b)
            elif (a - d).is_positive:
                return True
            elif (c - b).is_positive:
                return other.new(c, d)
            elif (b - c).is_positive:
                return True
        elif b == c:
            if a == d:
                if ((self.new == Inequality)
                    or (other.__class__ == Inequality)):
                    return True
                elif a == c:
                    return False
                else:
                    return Unequality(c, d)
            elif b == d:
                if ( other.new == Inequality ):
                    return True
                else:
                    return self.new(a, d)
            elif (d - a).is_positive:
                return True
            elif (d - b).is_positive:
                return True
            elif (b - d).is_positive:
                return self._class__(a, b)
        elif b == d:
            if  (b - c).is_positive:
                return True
            elif (c - b).is_positive:
                return self.new(a, b)
            elif (c - a).is_positive:
                return self.new(a, b)
            elif (a - c).is_positive:
                return other.new(c, b)
            elif (a - d).is_positive:
                return other.new(c, b)
            elif (d - a).is_positive:
                return True
            elif a == d:
                if self.new == Inequality:
                    return True
                else:
                    return other.new(c, b)
        elif a == d:
            if (b - c).is_positive:
                return True
            if (b - d).is_positive:
                return True
            if (d - b).is_positive:
                return other.new(c, b)
            if (a - c).is_positive:
                return True
            if (a - c).is_positive:
                return self.new(a, b)
        raise NoUnionError("No meaningful union")

