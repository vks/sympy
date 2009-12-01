from sympy.core import Symbol

_all = list('abcdefghijklmnopqrstuvwxyz')
for _s in _all:
    exec "%s = Symbol('%s')" % (_s, _s)
del _all, _s, Symbol
