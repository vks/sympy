from sympy.core import Symbol

_alpha = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
for _s in _alpha:
    exec "%s = Symbol('%s')" % (_s, _s)

__all__ = list(
    set(list(_alpha)).difference(set(list('CEINOQS')))
)

del _alpha, _s, Symbol

