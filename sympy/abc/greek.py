from sympy.core import Symbol

_all = 'alpha beta gamma delta epsilon zeta eta theta iota kappa '\
  'mu nu xi omicron pi rho sigma tau upsilon phi chi psi omega'.split()
for _s in _all:
    exec "%s = Symbol('%s')" % (_s, _s)
del _all, _s, Symbol
