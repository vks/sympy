#!/usr/bin/env python

import os
import sympy
from sympy import test

sympy_dir = os.path.dirname(sympy.__file__)

# If you uncomment this, everything works.
#test(os.path.join(sympy_dir, 'series', 'tests', 'test_nseries.py'))
test(os.path.join(sympy_dir, 'core', 'tests', 'test_wester.py'))
test(os.path.join(sympy_dir, 'series', 'tests', 'test_nseries.py'))
