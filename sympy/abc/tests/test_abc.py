import warnings
from sympy.utilities.pytest import raises

def test_abc():
    warnings.simplefilter('ignore')
    from sympy import *
    from sympy.abc.greek import *
    assert alpha
    raises(NameError, 'x')
    from sympy.abc.lower import *
    assert x and y and a and s
    raises(NameError, 'A')
    from sympy.abc.upper import *
    assert A.is_Symbol
    assert not isinstance(S, Symbol)
    from sympy.abc.upper import S
    assert S.is_Symbol
    warnings.resetwarnings()

