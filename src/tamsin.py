#!/usr/bin/env python
# encoding: UTF-8

import codecs
import sys

DEBUG = False

def debug(x):
    if DEBUG:
        print x.encode('ascii', 'ignore')


class TamsinParseError(ValueError):
    pass


class Term(object):
    def __init__(self, name, contents=None):
        self.name = name
        if contents is None:
            contents = []
        self.contents = contents

    def expand(self, context):
        """Expands this term, returning a new term where replacing all
        (VAR x) with the value of x in the given context.

        """
        return Term(self.name, [x.expand(context) for x in self.contents])

    def __str__(self):
        if not self.contents:
            return self.name
        return "%s(%s)" % (
            self.name, ', '.join([str(x) for x in self.contents])
        )

    def __repr__(self):
        # sigh
        return str(self)


class Variable(Term):
    def __init__(self, name):
        assert name[0].isupper()
        self.name = name
        self.contents = []

    def expand(self, context):
        return context.fetch(self.name)


class Concat(Term):
    def __init__(self, lhs, rhs):
        assert isinstance(lhs, Term)
        assert isinstance(rhs, Term)
        self.lhs = lhs
        self.rhs = rhs

    def expand(self, context):
        lhs = self.lhs.expand(context)
        rhs = self.rhs.expand(context)
        return Term(str(lhs) + str(rhs))

    def __str__(self):
        return "%s + %s" % (self.lhs, self.rhs)


class Scanner(object):
    def __init__(self, buffer):
        """Calls scan() for you!"""
        debug("setting buffer to '%s'" % buffer)
        self.buffer = buffer
        self.position = 0
        self.token = None
        self.scan()

    def eof(self):
        return self.position >= len(self.buffer)

    def chop(self, amount):
        if self.eof():
            return None
        result = self.buffer[self.position:self.position+amount]
        #debug("chopped: '%s'" % result)
        self.position += amount
        return result

    def startswith(self, strings):
        for s in strings:
            if self.buffer[self.position:self.position+len(s)] == s:
                return True
        return False

    def isalnum(self):
        return self.buffer[self.position].isalnum()

    def error(self, expected):
        report = self.buffer[self.position:self.position+20]
        if len(report) == 20:
            report += '...'
        #raise ValueError((expected, self.token, report))
        raise ValueError(u"Expected %s, found '%s' at '%s...'" %
                         (expected, self.token, report))

    def clone(self, class_=None):
        if class_ is None:
            class_ = self.__class__
        n = class_(self.buffer)
        n.position = self.position
        n.token = self.token
        return n

    def scan(self):
        self.reset_position = self.position
        self.scan_impl()
        debug("scanned: '%s'" % self.token)

    def switch(self, class_):
        # 'putback' the token
        debug("reset position %s, position %s, putbacking '%s'" %
            (self.reset_position, self.position,
                self.buffer[self.reset_position:self.position-self.reset_position+1])
        )
        self.position = self.reset_position
        self.token = None
        new_scanner = self.clone(class_=class_)
        new_scanner.scan()
        return new_scanner

    def consume(self, t):
        #print repr(self.token), repr(t)
        if self.token == t:
            self.scan()
            return t
        else:
            return None
    
    def expect(self, t):
        r = self.consume(t)
        if r is None:
            self.error("'%s'" % t)
        return r


class TamsinScanner(Scanner):
    def scan_impl(self):
        while self.startswith((' ', '\t', '\r', '\n')):
            self.chop(1)

        if self.eof():
            self.token = None
            return

        if self.startswith(('&&', '||')):
            self.token = self.chop(1)
            self.chop(1)
            return
        
        if self.startswith(('=', '(', ')', '[', ']', '{', '}',
                            '|', '&', u'→', ',', '.', '@', u'•')):
            self.token = self.chop(1)
            return

        if self.startswith(('"',)):
            self.token = '"'
            self.chop(1)
            while not self.eof() and not self.startswith('"'):
                self.token += self.chop(1)
            self.chop(1)  # chop ending quote
            return

        if self.startswith((u'「',)):
            self.token = u'「'
            self.chop(1)
            while not self.eof() and not self.startswith(u'」'):
                self.token += self.chop(1)
            self.chop(1)  # chop ending quote
            return

        if not self.eof() and self.isalnum():
            self.token = ''
            while not self.eof() and self.isalnum():
                self.token += self.chop(1)
            return

        self.token = self.buffer[0]
        self.error('identifiable character')


class RawScanner(Scanner):
    def scan_impl(self):
        if self.eof():
            self.token = None
            return
        self.token = self.chop(1)


class Parser(object):
    def __init__(self, buffer):
        self.scanner = TamsinScanner(buffer)

    def eof(self):
        return self.scanner.eof()
    def chop(self, amount):
        return self.scanner.chop(amount)
    def startswith(self, strings):
        return self.scanner.startswith(strings)
    def isalnum(self):
        return self.scanner.isalnum()
    def error(self, expected):
        return self.scanner.error(expected)
    def scan(self):
        return self.scanner.scan()
    def consume(self, t):
        return self.scanner.consume(t)
    def expect(self, t):
        return self.scanner.expect(t)

    def grammar(self):
        prods = [self.production()]
        while self.scanner.token is not None:
            prods.append(self.production())
        
        return ('PROGRAM', prods)
    
    def production(self):
        name = self.scanner.token
        self.scan()
        args = []
        if self.consume('('):
            if self.scanner.token != ')':
                args.append(self.term())
                while self.consume(','):
                    args.append(self.term())
            self.expect(')')
        self.expect('=')
        e = self.expr0()
        self.expect('.')
        return ('PROD', name, args, e)
    
    def expr0(self):
        lhs = self.expr1()
        while self.consume('|'):
            rhs = self.expr1()
            lhs = ('OR', lhs, rhs)
        return lhs

    def expr1(self):
        lhs = self.expr2()
        while self.consume('&'):
            rhs = self.expr2()
            lhs = ('AND', lhs, rhs)
        return lhs

    def expr2(self):
        lhs = self.expr3()
        if self.consume('with'):
            scanner_name = self.scanner.token
            self.scan()
            lhs = ('WITH', lhs, scanner_name)
        return lhs

    def expr3(self):
        lhs = self.expr4()
        if self.consume(u'→'):
            v = self.variable()
            lhs = ('SEND', lhs, v)
        return lhs

    def expr4(self):
        if self.consume('('):
            e = self.expr0()
            self.expect(')')
            return e
        elif self.consume('['):
            e = self.expr0()
            self.expect(']')
            return ('OR', e, ('RETURN', Term('nil')))
        elif self.consume('{'):
            e = self.expr0()
            self.expect('}')
            return ('WHILE', e)
        elif self.scanner.token and self.scanner.token[0] == '"':
            literal = self.scanner.token[1:]
            self.scan()
            return ('LITERAL', literal)
        elif self.consume('set'):
            v = self.variable()
            self.expect("=")
            t = self.term()
            return ('SET', v, t)
        elif self.consume('return'):
            t = self.term()
            return ('RETURN', t)
        elif self.consume('fail'):
            return ('FAIL',)
        elif self.consume('print'):
            t = self.term()
            return ('PRINT', t)
        else:
            name = self.scanner.token
            self.scan()
            args = []
            if self.consume('('):
                if self.scanner.token != ')':
                    args.append(self.term())
                    while self.consume(','):
                        args.append(self.term())
                self.expect(')')
            ibuf = None
            if self.consume('@'):
                ibuf = self.term()
            return ('CALL', name, args, ibuf)

    def variable(self):
        if self.scanner.token[0].isupper():
            var = self.scanner.token
            self.scan()
            return Variable(var)
        else:
            self.error('variable')

    def term(self):
        lhs = self.term1()
        while self.consume(u'•'):
            rhs = self.term1()
            lhs = Concat(lhs, rhs)
        return lhs

    def term1(self):
        if self.scanner.token[0].isupper():
            return self.variable()
        elif self.scanner.token[0].isalnum() or self.scanner.token[0] == u'「':
            atom = self.scanner.token
            if atom[0] == u'「':
                atom = atom[1:]
            self.scan()
            subs = []
            if self.consume('('):
                if self.scanner.token != ')':
                    subs.append(self.term())
                while self.consume(','):
                    subs.append(self.term())
                self.expect(')')
            return Term(atom, subs)
        else:
            self.error('term')


class Context(object):
    def __init__(self):
        self.scopes = []

    def push_scope(self, purpose):
        debug("pushing new scope for %r" % purpose)
        self.scopes.append({})
        debug("SCOPES NOW: %r" % self.scopes)

    def pop_scope(self, purpose):
        debug("popping scope for %r" % purpose)
        self.scopes.pop()
        debug("SCOPES NOW: %r" % self.scopes)

    def clone(self):
        n = Context()
        for scope in self.scopes:
            n.scopes.append(scope.copy())
        return n

    def fetch(self, name):
        debug("fetching %s (it's %r, in %r)" %
            (name, self.scopes[-1].get(name, 'undefined'), self.scopes[-1])
        )
        return self.scopes[-1][name]

    def store(self, name, value):
        debug("updating %s (was %s) to %r" %
            (name, self.scopes[-1].get(name, 'undefined'), value)
        )
        self.scopes[-1][name] = value


class Interpreter(object):
    def __init__(self, ast, buffer):
        self.program = ast
        self.scanner = TamsinScanner(buffer)
        self.context = Context()

    ### grammar stuff ---------------------------------------- ###
    
    def find_productions(self, name):
        productions = []
        for ast in self.program[1]:
            if ast[1] == name:
                productions.append(ast)
        if not productions:
            raise ValueError("No '%s' production defined" % name)
        return productions

    ### term matching
    
    def match_all(self, patterns, values):
        """Returns a dict of bindings if all values match all patterns,
        or False if there was a mismatch.

        """
        i = 0
        bindings = {}
        while i < len(patterns):
            sub = self.match_terms(patterns[i], values[i])
            if sub == False:
                return False
            bindings.update(sub)
            i += 1
        return bindings
    
    def match_terms(self, pattern, value):
        """Returns a dict of bindings if the values matches the pattern,
        or False if there was a mismatch.

        """
        if isinstance(pattern, Variable):
            # TODO: check existing binding!  oh well, assume unique for now.
            return {pattern.name: value}
        elif isinstance(pattern, Term):
            i = 0
            if pattern.name != value.name:
                return False
            bindings = {}
            while i < len(pattern.contents):
                b = self.match_terms(pattern.contents[i], value.contents[i])
                if b == False:
                    return False
                bindings.update(b)
                i += 1
            return bindings

    ### interpreter proper ---------------------------------- ###
    
    def interpret(self, ast, bindings=None):
        debug("interpreting %s" % repr(ast))
        if ast[0] == 'PROGRAM':
            mains = self.find_productions('main')
            return self.interpret(mains[0])
        elif ast[0] == 'PROD':
            self.context.push_scope(ast[1])
            if bindings:
                for name in bindings.keys():
                    self.context.store(name, bindings[name])
            debug("INTERPRETING RULE %s" % repr(ast[3]))
            x = self.interpret(ast[3])
            debug("FINISHED INTERPRETING RULE %s" % repr(ast[3]))
            self.context.pop_scope(ast[1])
            return x
        elif ast[0] == 'CALL':
            name = ast[1]
            args = ast[2]
            ibuf = ast[3]
            prods = self.find_productions(name)
            debug("candidate productions: %r" % prods)
            args = [x.expand(self.context) for x in args]
            for prod in prods:
                formals = prod[2]
                debug("formals: %r, args: %r" % (formals, args))
                bindings = self.match_all(formals, args)
                debug("bindings: %r" % bindings)
                if bindings != False:
                    saved_scanner_state = None
                    if ibuf is not None:
                        ibuf = ibuf.expand(self.context)
                        debug("expanded ibuf: %r" % ibuf)
                        saved_scanner = self.scanner.clone()
                        self.scanner = (self.scanner.__class__)(str(ibuf))
                    x = self.interpret(prod, bindings=bindings)
                    if ibuf is not None:
                        self.scanner = saved_scanner
                    return x
            raise ValueError("No '%s' production matched arguments %r" %
                (name, args)
            )
        elif ast[0] == 'SEND':
            result = self.interpret(ast[1])
            assert isinstance(ast[2], Variable), ast
            self.context.store(ast[2].name, result)
            return result
        elif ast[0] == 'SET':
            assert isinstance(ast[1], Variable), ast
            assert isinstance(ast[2], Term), ast
            result = ast[2].expand(self.context)
            self.context.store(ast[1].name, result)
            return result
        elif ast[0] == 'AND':
            lhs = ast[1]
            rhs = ast[2]
            value_lhs = self.interpret(lhs)
            value_rhs = self.interpret(rhs)
            return value_rhs
        elif ast[0] == 'OR':
            lhs = ast[1]
            rhs = ast[2]
            saved_context = self.context.clone()
            saved_scanner = self.scanner.clone()
            try:
                return self.interpret(lhs)
            except TamsinParseError as e:
                self.context = saved_context
                self.scanner = saved_scanner
                return self.interpret(rhs)
        elif ast[0] == 'RETURN':
            return ast[1].expand(self.context)
        elif ast[0] == 'FAIL':
            raise TamsinParseError("fail")
        elif ast[0] == 'PRINT':
            val = ast[1].expand(self.context)
            print val
            return val
        elif ast[0] == 'WITH':
            sub = ast[1]
            scanner_name = ast[2]
            if scanner_name == 'tamsin':
                new_scanner_class = TamsinScanner
            elif scanner_name == 'raw':
                new_scanner_class = RawScanner
            else:
                raise ValueError("No such scanner '%s'" % scanner_name)
            self.scanner = self.scanner.switch(new_scanner_class)
            result = self.interpret(sub)
            return result
        elif ast[0] == 'WHILE':
            result = Term('nil')
            while True:
                saved_context = self.context.clone()
                saved_scanner = self.scanner.clone()
                try:
                    result = self.interpret(ast[1])
                except TamsinParseError as e:
                    self.context = saved_context
                    self.scanner = saved_scanner
                    return result
        elif ast[0] == 'LITERAL':
            debug('expecting %s, token is %s' % (ast[1], self.scanner.token))
            if self.scanner.token == ast[1]:
                self.scanner.scan()
                return Term(ast[1])
            else:
                raise TamsinParseError("expected '%s' found '%s'" %
                    (ast[1], self.scanner.token)
                )
        else:
            raise NotImplementedError(repr(ast))


def main(args):
    global DEBUG
    if args[0] == '--debug':
        DEBUG = True
        args = args[1:]
    if args[0] == 'parse':
        with codecs.open(args[1], 'r', 'UTF-8') as f:
            contents = f.read()
            parser = Parser(contents)
            ast = parser.grammar()
            print repr(ast)
    elif args[0] == 'run':
        with codecs.open(args[1], 'r', 'UTF-8') as f:
            contents = f.read()
            parser = Parser(contents)
            ast = parser.grammar()
            debug(repr(ast))
            interpreter = Interpreter(ast, sys.stdin.read())
            result = interpreter.interpret(ast)
            print str(result)
    else:
        raise ValueError("first argument must be 'parse' or 'run'")


if __name__ == '__main__':
    main(sys.argv[1:])
