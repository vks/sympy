"""Boolean algebra module for SymPy"""
from sympy.core import Basic, Function, sympify, Symbol, NoUnionError
from sympy.utilities import flatten, make_list
from sympy.core.operations import LatticeOp
from sympy.core.relational import Relational

class BooleanFunction(Function):
    """Boolean function is a function that lives in a boolean space
    It is used as base class for And, Or, Not, etc.
    """
    @staticmethod
    def _permute(l, ret=None):
        if ret == None:
            return BooleanFunction._permute(l[1:], ret=l[0])
        if len(l) == 0:
            return ret
        rr = []
        for r in ret:
            for term in l[0]:
                rr.append(And(r, term))
        return BooleanFunction._permute(l[1:], ret=rr)

    def _canonize(self, **hints):
        rel = to_cnf(self)
        if isinstance(rel, Or):
            return(rel)
        if not isinstance(rel, BooleanFunction):
            return rel
        args = []
        for arg in rel.args:
            if type(arg) is not Or:
                args.append([arg])
            else:
                args.append(list(arg.args))
        terms = self._permute(args)
        return Or(*terms)

    def doit(self, **hints):
        """
        Simplify logic expression by intersection and union of relational and interval terms.
        Examples:
            >>> from sympy import *
            >>> from sympy.logic.boolalg import And, Not, Or, to_cnf
            >>> x, l1, l2, l3=symbols("x l1 l2 l3")
            >>> c=Or(And(0 <= x, x <= l1 + l2, l1 < 0), And(0 <= x, x <= l1 + l2, l1 + l2 + l3 < 0))
            >>> x1, l11, l21, l31=symbols("x1 l11 l21 l31", real=True, positive=True)
            >>> d=c.subs([(x, x1), (l1, l11), (l2, l21), (l3, l31)])
            >>> d.doit()
            False
        """
        r = to_cnf(self)
        if isinstance(r, BooleanFunction):
            r = r._doit(**hints)
        if isinstance(r, BooleanFunction):
            r = r._canonize(**hints)
        if isinstance(r, BooleanFunction):
            r = r._doit(**hints)
        return r

    def _doit(self, **hints):
        """Try to symplify the boolean function by looking for
        terms occuring more than once, and using
        a and b = a intersection b
        and
        a or b = a union b
        """
        if not hasattr(self, '_set_method'):
            #we can do it only for And and Or
            return self
        setmethod = self._set_method
        terms = []
        # doit for all terms
        for term in self.args:
            term = term.doit(**hints)
            terms.append(term)
        terms2 = []
        # drop terms which are not first occurance
        for term in terms:
            if term in terms2:
                continue
            #and if there are two complement terms, we return
            # True or false
            if hasattr(term, 'complement'):
                if term.complement() in terms2:
                    return self.__class__(True, False)
            terms2.append(term)
        terms3 = []
        dealtwith = []
        # now we do union for Or, intersection for And
        for i, term in enumerate(terms2):
            if i in dealtwith:
                continue
            if hasattr(term, setmethod):
                # FIXME python sets are not handled here
                # sympify should convert them to sympy.core.sets.Set
                for j, term2 in enumerate(terms2):
                    if (j not in dealtwith) and (i <= j):
                        try:
                            term = getattr(term, setmethod)(term2)
                            dealtwith.append(j)
                            if hasattr(term, 'doit'):
                                term = term.doit(**hints)
                        except NoUnionError:
                            pass
                        if not hasattr(term, setmethod):
                            break
            if term not in terms3:
                terms3.append(term)
        if len(terms3) == 1:
            return terms3[0]
        return self.__class__(*terms3)
    pass

class And(LatticeOp, BooleanFunction):
    """
    Logical AND function.

    It evaluates its arguments in order, giving False immediately if any of them
    are False, and True if they are all True.

    Examples:
        >>> from sympy.core import symbols
        >>> from sympy.abc import x, y
        >>> x & y
        And(x, y)

    """
    zero = False
    identity = True
    _set_method = "_intersection"

    @classmethod
    def eval(cls, *args):
        out_args = []
        for arg in args: # we iterate over a copy or args
            if hasattr(arg, 'eval') and (not isinstance(arg, BooleanFunction)):
                 arg = arg.eval(*arg.args)
            else:
                 arg = arg
            if arg is None:
                return None
            if isinstance(arg, bool):
                if not arg: return False
                else: continue
            out_args.append(arg)
        if len(out_args) == 0:
            return True
        if len(out_args) == 1:
            return out_args[0]
        sargs = sorted(flatten(out_args, cls=cls))
        return Basic.__new__(cls, *sargs)

class Or(LatticeOp, BooleanFunction):
    """
    Logical OR function

    It evaluates its arguments in order, giving True immediately if any of them are
    True, and False if they are all False.
    """
    zero = True
    identity = False
    _set_method = "_union"

    @classmethod
    def eval(cls, *args):
        out_args = []
        for arg in args: # we iterate over a copy or args
            if isinstance(arg, bool):
                if arg: return True
                else: continue
            out_args.append(arg)
        if len(out_args) == 0:
            return False
        if len(out_args) == 1:
            return out_args[0]
        sargs = sorted(flatten(out_args, cls=cls))
        return Basic.__new__(cls, *sargs)

class Xor(BooleanFunction):
    """Logical XOR (exclusive OR) function.
    returns True if an odd number of the arguments are True, and the rest are False.
    returns False if an even number of the arguments are True, and the rest are False.
    """
    @classmethod
    def eval(cls, *args):
        if not args: return False
        args = list(args)
        A = args.pop()
        while args:
            B = args.pop()
            A = Or(A & Not(B), (Not(A) & B))
        return A

class Not(BooleanFunction):
    """Logical Not function (negation)

    Note: De Morgan rules applied automatically"""
    @classmethod
    def eval(cls, *args):
        if len(args) > 1:
            return map(cls, args)
        arg = args[0]
        # apply De Morgan Rules
        if type(arg) is  And:
            return Or(*[Not(a) for a in arg.args])
        if type(arg) is Or:
            return And(*[Not(a) for a in arg.args])
        if type(arg) is bool:
            return not arg
        if type(arg) is Not:
            return arg.args[0]

    def doit(self, **hints):
        assert len(self.args) == 1, "Multiarg Not is Not supported"
        term= self.args[0]
        term = term.doit(**hints)
        if isinstance(term, Relational):
            return term.complement()
        return self.new(term)


class Nand(BooleanFunction):
    """Logical NAND function.
    It evaluates its arguments in order, giving True immediately if any
    of them are False, and False if they are all True.
    """
    @classmethod
    def eval(cls, *args):
        if not args:
            return False
        args = list(args)
        A = Not(args.pop())
        while args:
            B = args.pop()
            A = Or(A, Not(B))
        return A

class Nor(BooleanFunction):
    """Logical NOR function.
    It evaluates its arguments in order, giving False immediately if any
    of them are True, and True if they are all False.
    """
    @classmethod
    def eval(cls, *args):
        if not args:
            return False
        args = list(args)
        A = Not(args.pop())
        while args:
            B = args.pop()
            A = And(A, Not(B))
        return A

class Implies(BooleanFunction):
    pass

class Equivalent(BooleanFunction):
    """Equivalence relation.
    Equivalent(A, B) is True if and only if A and B are both True or both False
    """
    @classmethod
    def eval(cls, *args):
        return Basic.__new__(cls, *sorted(args))

### end class definitions. Some useful methods

def fuzzy_not(arg):
    """
    Not in fuzzy logic

    will return Not if arg is a boolean value, and None if argument
    is None

    >>> from sympy.logic.boolalg import fuzzy_not
    >>> fuzzy_not(True)
    False
    >>> fuzzy_not(None)
    >>> fuzzy_not(False)
    True

    """
    if arg is None:
        return
    return not arg

def conjuncts(expr):
    """Return a list of the conjuncts in the expr s.
    >>> from sympy.logic.boolalg import conjuncts
    >>> from sympy.abc import A, B
    >>> conjuncts(A & B)
    [A, B]
    >>> conjuncts(A | B)
    [Or(A, B)]

    """
    return make_list(expr, And)

def disjuncts(expr):
    """Return a list of the disjuncts in the sentence s.
    >>> from sympy.logic.boolalg import disjuncts
    >>> from sympy.abc import A, B
    >>> disjuncts(A | B)
    [A, B]
    >>> disjuncts(A & B)
    [And(A, B)]

    """
    return make_list(expr, Or)

def distribute_and_over_or(expr):
    """
    Given a sentence s consisting of conjunctions and disjunctions
    of literals, return an equivalent sentence in CNF.
    """
    if isinstance(expr, Or):
        for arg in expr.args:
            if isinstance(arg, And):
                conj = arg
                break
        else:
            return type(expr)(*expr.args)
        rest = Or(*[a for a in expr.args if a is not conj])
        return And(*map(distribute_and_over_or,
                   [Or(c, rest) for c in conj.args]))
    elif isinstance(expr, And):
        return And(*map(distribute_and_over_or, expr.args))
    else:
        return expr

def to_cnf(expr):
    """Convert a propositional logical sentence s to conjunctive normal form.
    That is, of the form ((A | ~B | ...) & (B | C | ...) & ...)

    Examples:

        >>> from sympy.logic.boolalg import to_cnf
        >>> from sympy.abc import A, B, C
        >>> to_cnf(~(A | B) | C)
        And(Or(C, Not(A)), Or(C, Not(B)))

    """
    expr = sympify(expr)
    expr = eliminate_implications(expr)
    return distribute_and_over_or(expr)

def eliminate_implications(expr):
    """Change >>, <<, and Equivalent into &, |, and ~. That is, return an
    expression that is equivalent to s, but has only &, |, and ~ as logical
    operators.
    """
    expr = sympify(expr)
    if (type(expr) is bool) or expr.is_Atom:
        return expr     ## (Atoms are unchanged.)
    args = map(eliminate_implications, expr.args)
    a, b = args[0], args[-1]
    if isinstance(expr, Implies):
        return (~a) | b
    elif isinstance(expr, Equivalent):
        return (a | Not(b)) & (b | Not(a))
    else:
        return type(expr)(*args)

def compile_rule(s):
    """Transforms a rule into a sympy expression
    A rule is a string of the form "symbol1 & symbol2 | ..."
    See sympy.assumptions.known_facts for examples of rules

    TODO: can this be replaced by sympify ?
    """
    import re
    return eval(re.sub(r'([a-zA-Z0-9_.]+)', r'Symbol("\1")', s), {'Symbol' : Symbol})


def to_int_repr(clauses, symbols):
    """
    takes clauses in CNF puts them into integer representation

    Examples:
        >>> from sympy.logic.boolalg import to_int_repr
        >>> from sympy.abc import x, y
        >>> to_int_repr([x | y, y], [x, y])
        [[1, 2], [2]]

    """
    def append_symbol(arg, symbols):
        if type(arg) is Not:
            return -(symbols.index(arg.args[0])+1)
        else:
            return symbols.index(arg)+1

    output = []
    for c in clauses:
        if type(c) is Or:
            t = []
            for arg in c.args:
                t.append(append_symbol(arg, symbols))
            output.append(t)
        else:
            output.append([append_symbol(c, symbols)])
    return output

