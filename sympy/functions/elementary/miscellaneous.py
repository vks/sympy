from sympy.core import S, C, sympify, Function

###############################################################################
############################# SQUARE ROOT FUNCTION ############################
###############################################################################

def sqrt(arg):
    # arg = sympify(arg) is handled by Pow
    return C.Pow(arg, S.Half)

###############################################################################
############################# MINIMUM and MAXIMUM #############################
###############################################################################

class Max(Function):
    """
    Return, if possible, the maximum value of the list.

    When number of arguments is equal one, then
    return this argument.

    When number of arguments is equal two, then
    return, if possible, the value from (a, b) that is >= the other.

    In common case, when the length of list greater than 2, the task
    is more complicated. Return only the arguments, which are greater
    than others, if it is possible to determine directional relation.

    If is not possible to determine such a relation, return a partially
    evaluated result.

    Assumptions are used to make the decision too.

    Example
    -------

    >>> from sympy import Max, Symbol, oo
    >>> from sympy.abc import x, y
    >>> p = Symbol('p', positive=True)
    >>> n = Symbol('n', negative=True)

    >>> Max(x, -2)
    Max(x, -2)

    >>> _.subs(x, 3)
    3

    >>> Max(p, -2)
    p

    >>> Max(x, y)
    Max(x, y)

    >>> Max(n, 8, p, 7, -oo)
    Max(p, 8)

    Algorithm
    ---------

    The task can be considered as the task for directional graph.
    The graph can contain connected components or not.

    So, dynamically search the vertexes which can be removed,
    remove them, and repeat removing until it is possible.

    Vertexes which can be removed are:
        - duplicates.
        - those who are related only with greater ones.

    At the same time isolated vertexes should not be removed.

    Assumption:
       - if A > B > C then A > C
       - if A==B then B can be removed

    See Also
    --------
    Min() : find minimum values

    """

    @classmethod
    def eval(cls, *values, **options):
        if len(values) == 0:
            raise ValueError("The Max function must have arguments")
        elif len(values) == 1:
            # trivial
            return values[0]
        elif len(values) == 2:
            # usual case
            x = values[0]
            y = values[1]
            if cls.is_connected(x, y):
                if x==y:
                    return x
                elif cls.is_greater(x, y):
                    return x
                elif cls.is_greater(y, x):
                    return y
            return None
        else:
            # common case
            values = cls.remove_duplicates(values)
            was_removed = True
            while was_removed:
                was_removed = False
                for i, v in enumerate(values):
                    if cls.can_be_removed(v, values):
                        was_removed = True
                        # remove from list
                        values = values[:i] + values[i+1:]
                        break
            if len(values) == 1:
                return values[0]
            return cls(*values, **{'evaluate': False})

    @classmethod
    def is_connected(cls, x, y):
        """
        Check if x and y are connected somehow.
        """
        if (x == y) or isinstance(x > y, bool) or isinstance(x < y, bool):
            return True
        if x.is_Number and y.is_Number:
            return True
        return False

    @classmethod
    def is_greater(cls, x, y):
        """
        Check if x > y.
        """
        if (x == y):
            return False
        if x.is_Number and y.is_Number:
            if x > y:
                return True
        xy = x > y
        if isinstance(xy, bool):
            if xy:
                return True
            return False
        yx = y > x
        if isinstance(yx, bool):
            if yx:
                return False # never occurs?
            return True
        return False

    @classmethod
    def remove_duplicates(cls, values):
        """
        Remove duplicates from the list.
        """
        return list(set(values))

    @classmethod
    def can_be_removed(cls, v, values):
        """
        Check whether the vertex can be removed from graph.

        This is the case when all other vertexes, which are connected
        with the current one, are greater.
        """
        res = False         # vertex might be isolated, should not be removed
        for v2 in values:
            if id(v) <> id(v2):
                if cls.is_connected(v, v2):
                    res = True  # therefore vertex is not isolated
                    if cls.is_greater(v, v2):
                        return False
        return res

class Min(Max):
    """
    Return, if possible, the minimum value of the list.

    Example
    -------

    >>> from sympy import Min, Symbol, oo
    >>> from sympy.abc import x, y
    >>> p = Symbol('p', positive=True)
    >>> n = Symbol('n', negative=True)

    >>> Min(x, -2)
    Min(x, -2)

    >>> _.subs(x, 3)
    -2

    >>> Min(p, -3)
    -3

    >>> Min(x, y)
    Min(x, y)

    >>> Min(n, 8, p, -7, p, oo)
    Min(-7, n)

    See Also
    --------
    Max() : find maximum values
    """
    @classmethod
    def is_less(cls, x, y):
        """
        Check if x < y.
        """
        if (x == y):
            return False
        if x.is_Number and y.is_Number:
            if x < y:
                return True
        xy = x < y
        if isinstance(xy, bool):
            if xy:
                return True
            return False
        yx = y < x
        if isinstance(yx, bool):
            if yx:
                return False # never occurs?
            return True
        return False

    @classmethod
    def is_greater(cls, x, y):
        """
        Polymorphism: revert the direction to opposite for all relations.
        """
        return cls.is_less(x, y)

