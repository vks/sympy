# doctests are disabled because of issue #1521
from sympy.core import Basic, Symbol
from sympy.logic.boolalg import And, Or, Not
import inspect

class AssumptionsContext(set):
    """Set representing assumptions.

    This is used to represent global assumptions, but you can also use this
    class to create your own local assumptions contexts. It is basically a thin
    wrapper to Python's set, so see its documentation for advanced usage.

    Examples:
        >>> from sympy import AssumptionsContext, Assume, Q
        >>> c = AssumptionsContext; c
        AssumptionsContext()
        >>> from sympy.abc import x
        >>> c.add(Assume(x, Q.real))
        >>> c
        AssumptionsContext([Assume(x, 'real', True)])
        >>> c.remove(Assume(x, Q.real))
        >>> c
        AssumptionsContext()
        >>> c.clear()

    """

    def add(self, *assumptions):
        """Add an assumption."""
        for a in assumptions:
            assert type(a) in (Assume, And, Or, Not), \
                    'can only store Assume, And, Or or Not'
            super(AssumptionsContext, self).add(a)

LOCALCONTEXT = '__sympy_local_assumptions'

def set_local_assumptions():
    """Set a local assumption context and return it.

    By default, this is done in the current local scope, this can be changed
    using the `scope` argument.

    This will overwrite any previous (local) assumptions."""
    f = inspect.currentframe().f_back
    c = AssumptionsContext()
    f.f_locals[LOCALCONTEXT] = c
    return c

def get_local_assumptions():
    """Return the current local assumption context.

    This can be in an outer scope if `set_local_assumptions()` has not been yet
    called in the current scope.

    If there is no defined assumption context in any scope, None is returned.
    """
    f = inspect.currentframe()
    while f.f_back is not None:
        f = f.f_back
        result = f.f_locals.get(LOCALCONTEXT)
        if result is not None:
            return result
    return None

class Assume(Basic):
    """New-style assumptions.

    >>> from sympy import Assume, Q
    >>> from sympy.abc import x
    >>> Assume(x, Q.integer)
    Assume(x, 'integer', True)
    >>> Assume(x, Q.integer, False)
    Assume(x, 'integer', False)
    >>> Assume( x > 1 )
    Assume(1 < x, 'relational', True)

    """
    def __init__(self, expr, key='relational', value=True):
        self._args = (expr, key, value)

    is_Atom = True # do not attempt to decompose this

    @property
    def expr(self):
        """
        Return the expression used by this assumption.

        Examples:
            >>> from sympy import Assume, Q
            >>> from sympy.abc import x
            >>> a = Assume(x+1, Q.integer)
            >>> a.expr
            1 + x

        """
        return self._args[0]

    @property
    def key(self):
        """
        Return the key used by this assumption.
        It is a string, e.g. 'integer', 'rational', etc.

        Examples:
            >>> from sympy import Assume, Q
            >>> from sympy.abc import x
            >>> a = Assume(x, Q.integer)
            >>> a.key
            'integer'

        """
        return self._args[1]

    @property
    def value(self):
        """
        Return the value stored by this assumptions.
        It's a boolean. True means that the assumption
        holds always, and False means the assumption
        does not hold

        Examples:
            >>> from sympy import Assume, Q
            >>> from sympy.abc import x
            >>> a = Assume(x, Q.integer)
            >>> a.value
            True
            >>> b = Assume(x, Q.integer, False)
            >>> b.value
            False

        """
        return self._args[2]

    def __eq__(self, other):
        if type(other) == Assume:
            return self._args == other._args
        return False

def eliminate_assume(expr, symbol=None):
    """
    Convert an expression with assumptions to an equivalent with all assumptions
    replaced by symbols.

    Assume(x, integer=True) --> integer
    Assume(x, integer=False) --> ~integer

    Examples:
        >>> from sympy.assumptions.assume import eliminate_assume
        >>> from sympy import Assume, Q
        >>> from sympy.abc import x
        >>> eliminate_assume(Assume(x, Q.positive))
        positive
        >>> eliminate_assume(Assume(x, Q.positive, False))
        Not(positive)

    """
    if type(expr) == Assume:
        if symbol is not None:
            if not expr.expr.has(symbol): return
        if expr.value: return Symbol(expr.key)
        return ~Symbol(expr.key)
    args = []
    for a in expr.args:
        args.append(eliminate_assume(a))
    return expr.func(*args)
