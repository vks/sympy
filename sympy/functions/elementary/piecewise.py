from sympy.core.basic import Basic, S
oo = S.Infinity
from sympy.core.function import Function, diff
from sympy.core.numbers import Number
from sympy.core.relational import Relational
from sympy.logic.boolalg import BooleanFunction, Not, And, Or
from sympy.core.sympify import sympify
from sympy.core.sets import Interval, Set, EmptySet, Union
from sympy import nan


from sympy.utilities.decorator import deprecated


class ExprCondPair(Basic):
    """Represents an expression, condition pair."""

    def __new__(cls, *args, **assumptions):
        if isinstance(args[0], cls):
            expr = args[0].expr
            cond = args[0].cond
        elif len(args) == 2:
            expr = sympify(args[0])
            cond = sympify(args[1])
        else:
            raise TypeError("args must be a (expr, cond) pair")
        return Basic.__new__(cls, expr, cond, **assumptions)

    @property
    def expr(self):
        return self.args[0]

    @property
    def cond(self):
        return self.args[1]

    def __iter__(self):
        yield self.expr
        yield self.cond


class Piecewise(Function):
    """
    Represents a piecewise function.

    Usage
    =====
      Piecewise( (expr,cond), (expr,cond), ... )
        - Each argument is a 2-tuple defining a expression and condition
        - The conds are evaluated in turn returning the first that is True.
          If any of the evaluated conds are not determined explicitly False,
          e.g. x < 1, the function is returned in symbolic form.
        - If the function is evaluated at a place where all conditions are False,
          a ValueError exception will be raised.
        - Pairs where the cond is explicitly False, will be removed.

    Examples
    ========
      >>> from sympy import Piecewise, log
      >>> from sympy.abc import x
      >>> f = x**2
      >>> g = log(x)
      >>> p = Piecewise( (0, x<-1), (f, x<=1), (g, True))
      >>> p.subs(x,1)
      1
      >>> p.subs(x,5)
      log(5)

    """

    nargs = None
    is_Piecewise = True

    def __new__(cls, *args, **options):
        from sympy.solvers.solvers import solve
        from sympy.core.symbol import Symbol
        # (Try to) sympify args first
        newargs = []
        conds = False
        for ec in args:
            pair = ExprCondPair(*ec)
            cond_type = type(pair.cond)
            if not (cond_type is bool or issubclass(cond_type, Relational) or \
                    issubclass(cond_type, Number) or issubclass(cond_type, BooleanFunction)):
                raise TypeError, \
                    "Cond %s is of type %s, but must be a bool," \
                    " Relational, Logic or Number" % (pair.cond, cond_type)
            cond = And(pair.cond , ( Not(conds) ))
            if hasattr(cond, 'doit'):
                cond = cond.doit()
            conds = Or(conds, pair.cond)
            if hasattr(conds, 'doit'):
                conds = conds.doit()
            if cond is not False:
                newargs.append(ExprCondPair(pair.expr, cond))
        r = cls.eval(*newargs)

        if r is None:
            return Basic.__new__(cls, *newargs, **options)
        else:
            return r

    def __getnewargs__(self):
        # Convert ExprCondPair objects to tuples.
        args = []
        for expr, condition in self.args:
            args.append((expr, condition))
        return tuple(args)

    @classmethod
    def eval(cls, *args):
        # Check for situations where we can evaluate the Piecewise object.
        # 1) Hit an unevaluatable cond (e.g. x<1) -> keep object
        # 2) Hit a true condition -> return that expr
        # 3) Remove false conditions, if no conditions left -> raise ValueError
        all_conds_evaled = True
        non_false_ecpairs = []
        for expr, cond in args:
            cond_eval = cls.__eval_cond(cond)
            if cond_eval is None:
                all_conds_evaled = False
                non_false_ecpairs.append( (expr, cond) )
            elif cond_eval:
                if all_conds_evaled:
                    return expr
                non_false_ecpairs.append( (expr, cond) )
        if len(non_false_ecpairs) != len(args):
            return Piecewise(*non_false_ecpairs)

        # Count number of arguments.
        nargs = 0
        for expr, cond in args:
            if hasattr(expr, 'nargs'):
                nargs = max(nargs, expr.nargs)
            elif hasattr(expr, 'args'):
                nargs = max(nargs, len(expr.args))
        if nargs:
            cls.narg = nargs
        return None

    def doit(self, **hints):
        newargs = []
        for e, c in self.args:
            if hints.get('deep', True):
                if isinstance(e, Basic):
                    e = e.doit(**hints)
                if isinstance(c, Basic):
                    c = c.doit(**hints)
            newargs.append((e, c))
        return Piecewise(*newargs)

    def _eval_integral(self, x):
        from sympy.integrals import integrate
        return  Piecewise(*[(integrate(e, x), c) for e, c in self.args])
    def _intervals(self, sym, a, b):
        # Determine what intervals the expr, cond pairs affect.
        # 1) If cond is True, then log it as default
        # 1.1) Currently if cond can't be evaluated, throw NotImplentedError.
        # 2) For each inequality, if previous cond defines part of the interval
        #    update the new conds interval.
        #    -  eg x < 1, x < 3 -> [oo, 1], [1, 3] instead of [oo, 1], [oo, 3]
        # 3) Sort the intervals to make it easier to find correct exprs
        from sympy.solvers.solvers import solve
        int_expr = []
        default = None
        fullset = EmptySet()
        for expr, cond in self.args:
            if isinstance(cond, bool) or cond.is_Number:
                if cond:
                    default = expr
                    break
                else:
                    continue
            for range in solve(cond, sym):
                if isinstance(range, Set):
                   if isinstance(range, EmptySet):
                      continue
                else:
                   raise NotImplementedError(
                       "is it possible to have no Set as solution of the condition?")
                r = ( - fullset ).intersect(range)
                fullset = fullset + range
                if not isinstance(r, EmptySet):
                    int_expr.append((r, expr))

        if default is not None:
            for (range, expr) in int_expr:
                fullset = fullset + range
            holes = - fullset
            if not isinstance(holes, EmptySet):
                if isinstance(holes, Interval):
                    int_expr.append((holes, default,))
                elif isinstance(holes, Union):
                    for range in holes.args:
                     int_expr.append((range, default,))
                else:
                    raise ProgrammingError, "e?"
        int_expr.sort(key = lambda x:x[0].start)
        return int_expr

    def _eval_interval(self, x, a, b):
        """Evaluate the function along the sym in a given interval ab."""
        # FIXME: Currently only supports conds of type sym < Num, or Num < sym
        mul = 1
        if a > b:
            a, b, mul = b, a, -1

        i = self._intervals(x, a, b)
        from sympy.series import limit
        lastend = None
        pieces = []
        for ( range, v ) in i:
            adduend = limit(v, x, range.end, dir="-")
            if lastend is None:
                p = (v, range.contains(x))
                lastend=adduend
            else:
                minuend = limit(v, x, range.start, dir="+")
                p = (v - minuend + lastend, range.contains(x))
                lastend = adduend - minuend + lastend
            pieces.append(p)
        r = Piecewise(*pieces)
        return  mul*(r.subs(x, b) - r.subs(x, a))

        # FIXME: Currently only supports conds of type sym < Num, or Num < sym
        mul = 1
        if a > b:
            a, b, mul = b, a, -1
        return mul*(self.subs(sym, b) - self.subs(sym, a))


        int_expr = self._intervals(sym, a, b)
        # Finally run through the intervals and sum the evaluation.
        ret_fun = 0
        for range, expr in int_expr:
            ret_fun += expr._eval_interval(sym, max(a, range.start), min(b, range.end))
        return mul * ret_fun

    def _eval_derivative(self, s):
        return Piecewise(*[(diff(e, s), c) for e, c in self.args])

    def _eval_subs(self, old, new):
        if self == old:
            return new
        new_args = []
        for e, c in self.args:
            if isinstance(c, bool):
                new_args.append((e._eval_subs(old, new), c))
            else:
                new_args.append((e._eval_subs(old, new), c._eval_subs(old, new)))
        return Piecewise( *new_args )

    @classmethod
    def __eval_cond(cls, cond):
        """Returns S.One if True, S.Zero if False, or None if undecidable."""
        if hasattr(cond, 'doit'):
            cond.doit()
        if (type(cond) == bool or cond.is_number or 
            (isinstance(cond, Relational) and cond.args[0].is_Number and
              cond.args[1].is_Number)):
            if cond: return S.One
            return S.Zero
        elif ( not isinstance(cond, BooleanFunction)) and cond.is_number:
            if cond > 0: return S.One
            return S.Zero
        return None

def _pw_vs_pw(expr, args):
    if not isinstance(expr, Piecewise):
        return args
    n_a = []
    for expr, cond in args:
        if isinstance(expr, Piecewise):
            for (e1, c1) in expr.args:
                if isinstance(c1, bool):
                    (c1, cond) = (cond, c1)
                n_a.append(ExprCondPair(e1, c1 & cond))
        else:
            n_a.append(ExprCondPair(expr, cond))
    return n_a


def piecewise_fold(expr):
    """
    Takes an expression containing a piecewise function and returns the
    expression in piecewise form.

    >>> from sympy import Piecewise, piecewise_fold
    >>> from sympy.abc import x
    >>> p = Piecewise((x, x < 1), (1, 1 <= x))
    >>> piecewise_fold(x*p)
    Piecewise((x**2, x < 1), (x, 1 <= x))

    """
    if not isinstance(expr, Basic) or not expr.has_piecewise:
        return expr
    new_args = map(piecewise_fold, expr.args)
    if type(expr) is ExprCondPair:
        return ExprCondPair(*new_args)
    piecewise_args = []
    for n, arg in enumerate(new_args):
        if type(arg) is Piecewise:
            piecewise_args.append(n)
    if len(piecewise_args) > 0:
        n = piecewise_args[0]
        new_args = [(expr.__class__(*(new_args[:n] + [e] + new_args[n + 1:])), c) \
                        for e, c in new_args[n].args]
        if len(piecewise_args) > 1:
            return piecewise_fold(Piecewise(*_pw_vs_pw(expr, new_args)))
    return Piecewise(*_pw_vs_pw(expr, new_args))

