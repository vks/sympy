import re

##########
# PARSER #
##########

def expression(rbp=0):
    # TODO: docstring
    global token
    t = token
    token = next()
    left = t.nud()
    while rbp < token.lbp:
        t = token
        token = next()
        left = t.led(left)
    return left

def advance(id=None):
    """Check that current token has a given id, before fetching next token."""
    global token
    if id and token.id != id:
        raise SyntaxError("Expected %r" % id)
    token = next()

def parse(program):
    """Parse a programm given as a string."""
    global token, next
    next = tokenize(program).next
    token = next()
    return expression()

def test(program, eval_sympy=True):
    """Show input and parsed result."""
    print ">>>", program
    p = str(parse(program))
    print p
    if eval_sympy:
        from sympy import *
        try:
            p = srepr(eval(p))
            print '=>', p
        except:
            pass
    print

###########
# SYMBOLS #
###########

symbol_table = {}

class symbol_base(object):
    """Base class for a symbol to be parsed."""
    id = None # node/token type name
    value = None # used by literals
    first = second = third = None # use by tree nodes

    def nud(self):
        """Null denotation.

        When a token appears at he beginning of a language construct.
        """
        raise SyntaxError("Syntax error: %r" % self.id)

    def led(self, left):
        """Left Denotation.

        Appears inside a construct (to the left of the rest).
        """
        raise SyntaxError("Unknown operator: %r" % self.id)

    def __repr__(self):
        s = set(['name', 'Real', 'Integer'])
        if self.id in s:
            return "%s(%s)" % (self.id, self.value)
        out = [self.first, self.second, self.third]
        out = map(str, filter(None, out))
        if not self.name is None:
            name = self.name
        else:
            name = self.id
        return name + '(' + ", ".join(out) + ')'

def symbol(id, bp=0, name=None):
    """Register a symbol.

    id : token identifier
    bp : binding power
    name : name for representation (used instead of id)
    """
    try:
        s = symbol_table[id]
    except KeyError:
        class s(symbol_base):
            pass
        s.__name__ = "symbol-" + id # for debugging
        s.id = id
        s.name = name
        s.value = None
        s.lbp = bp
        symbol_table[id] = s
    else:
        s.lbp = max(bp, s.lbp)
    return s

def infix(id, bp, name=None):
    """Register an infix operator."""
    def led(self, left):
        self.first = left
        self.second = expression(bp)
        return self
    symbol(id, bp, name).led = led

def infix_r(id, bp, name=None):
    """Register an infix operator with right associativity."""
    def led(self, left):
        self.first = left
        self.second = expression(bp - 1)
        return self
    symbol(id, bp, name).led = led

def prefix(id, bp, name=None):
    """Register a prefix operator."""
    def nud(self):
        self.first = expression(bp)
        self.second = None
        return self
    symbol(id, name=name).nud = nud

def method(s):
    """Pick up function name and attach given symbol."""
    assert issubclass(s, symbol_base)
    def bind(fn):
        setattr(s, fn.__name__, fn)
    return bind

#########
# MODEL #
#########

infix_r("or", 30); infix_r("and", 40); prefix("not", 50)

infix("<", 60); infix("<=", 60)
infix(">", 60); infix(">=", 60)
infix("!=", 60); infix("==", 60)

infix("|", 70); infix("^", 80); infix("&", 90)
infix("<<", 100); infix(">>", 100)

infix("+", 110, 'Add'); infix("-", 110)

infix("*", 120, 'Mul'); infix("/", 120); infix("//", 120)
infix("%", 120)

prefix("-", 130); prefix("+", 130); prefix("~", 130)

infix_r("**", 140, 'Pow')

symbol('name').nud = lambda self: self
symbol('Integer').nud = lambda self: self
symbol('Real').nud = lambda self: self
symbol('end')

symbol(")")

@method(symbol("("))
def nud(self):
    # parenthesized form; replaced by tuple former below
    expr = expression()
    advance(")")
    return expr

@method(symbol("("))
def led(self, left):
    self.first = left
    self.second = []
    if token.id != ")":
        while 1:
            self.second.append(expression())
            if token.id != ",":
                break
            advance(",")
    advance(")")
    return self

@method(symbol("("))
def nud(self):
    self.first = []
    comma = False
    if token.id != ")":
        while 1:
            if token.id == ")":
                break
            self.first.append(expression())
            if token.id != ",":
                break
            comma = True
            advance(",")
    advance(")")
    if not self.first or comma:
        return self # tuple
    else:
        return self.first[0]

def tokenize_python(program):
    import tokenize
    from cStringIO import StringIO
    type_map = {
        tokenize.NUMBER: "Real",
        tokenize.STRING: "(literal)", # TODO
        tokenize.OP: "operator",
        tokenize.NAME: "name",
        }
    for t in tokenize.generate_tokens(StringIO(program).next):
        try:
            yield type_map[t[0]], t[1]
        except KeyError:
            if t[0] == tokenize.NL:
                continue
            if t[0] == tokenize.ENDMARKER:
                break
            else:
                raise SyntaxError("Syntax error")
    yield "end", "end" # TODO: multiline supported or not?

names = set(['name', 'Integer', 'Real'])
def tokenize(program):
    """Tokenize the program given as a string."""
    if isinstance(program, list):
        source = program
    else:
        source = tokenize_python(program)
    for id, value in source:
        if 0: #id == "(literal)":
            symbol = symbol_table[id]
            s = symbol()
            s.value = value
        else:
            # name or operator
            symbol = symbol_table.get(value)
            if symbol: # operator
                s = symbol()
            elif id in names:
                symbol = symbol_table[id]
                s = symbol()
                s.value = value
            else:
                raise SyntaxError("Unknown operator (%r)" % id)
        yield s


if __name__ == '__main__':
    test("1")
    test("+1")
    test("-1")
    test("1 + 2")
    test("1+2+3")
    test("1+2*3")
    test("(1+2)*3")
    test("log(2*(1+10**3))")
    test("(1+x)*3")
    test("2.3")
    test("1.0+1.0j")

