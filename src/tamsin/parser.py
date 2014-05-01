# encoding: UTF-8

# Copyright (c)2014 Chris Pressey, Cat's Eye Technologies.
# Distributed under a BSD-style license; see LICENSE for more information.

from tamsin.term import Term, Variable, Concat
from tamsin.event import EventProducer
from tamsin.scanner import (
    EOF, Scanner, TamsinScannerEngine
)


class Parser(EventProducer):
    def __init__(self, buffer, listeners=None):
        self.listeners = listeners
        self.scanner = Scanner(buffer, listeners=self.listeners)
        self.scanner.push_engine(TamsinScannerEngine())
        self.aliases = {
            'eof': (0, ('PRODREF', '$', 'eof')),
            'any': (0, ('PRODREF', '$', 'any')),
            'print': (1, ('PRODREF', '$', 'print')),
            'fail': (1, ('PRODREF', '$', 'fail')),
            'return': (1, ('PRODREF', '$', 'return')),
        }

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
    def peek(self):
        return self.scanner.peek()
    def consume(self, t):
        return self.scanner.consume(t)
    def consume_any(self):
        return self.scanner.consume_any()
    def expect(self, t):
        return self.scanner.expect(t)

    def grammar(self):
        while self.consume('@'):
            self.pragma()
            self.expect('.')
        prods = [self.production()]
        while self.peek() is not EOF:
            prods.append(self.production())
        return ('PROGRAM', [], prods)

    def pragma(self):
        if self.consume('alias'):
            alias = self.consume_any()
            arity = int(self.consume_any())
            self.expect('=')
            prodref = self.prodref()
            self.aliases[alias] = (arity, prodref)
        elif self.consume('unalias'):
            alias = self.consume_any()
            del self.aliases[alias]
        else:
            self.error('pragma')
            
    def production(self):
        name = self.consume_any()
        formals = []
        if self.consume('('):
            if self.peek() != ')':
                formals.append(self.term())
                while self.consume(','):
                    formals.append(self.term())
            self.expect(')')
        elif self.consume('['):
            formals = self.expr0()
            self.expect(']')
        self.expect('=')
        body = self.expr0()
        self.expect('.')
        return ('PROD', name, formals, (), body)

    def expr0(self):
        lhs = self.expr1()
        while self.consume('|') or self.consume('||'):
            rhs = self.expr1()
            lhs = ('OR', lhs, rhs)
        return lhs

    def expr1(self):
        lhs = self.expr2()
        while self.consume('&') or self.consume('&&'):
            rhs = self.expr2()
            lhs = ('AND', lhs, rhs)
        return lhs

    def expr2(self):
        lhs = self.expr3()
        if self.consume('using'):
            prodref = self.prodref()
            lhs = ('USING', lhs, prodref)
        return lhs

    def expr3(self):
        lhs = self.expr4()
        if self.consume(u'→') or self.consume('->'):
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
            return ('OR', e,
                ('CALL', ('PRODREF', '$', 'return'), [Term('nil')], None)
            )
        elif self.consume('{'):
            e = self.expr0()
            self.expect('}')
            return ('WHILE', e)
        elif self.peek()[0] == '"':
            literal = self.consume_any()[1:-1]
            return ('CALL', ('PRODREF', '$', 'expect'), [Term(literal)], None)
        elif self.consume(u'«') or self.consume('<<'):
            t = self.term()
            if self.consume(u'»') or self.consume('>>'):
                return ('CALL', ('PRODREF', '$', 'expect'), [t], None)
            else:
                self.error("'>>'")
        elif self.consume('!'):
            e = self.expr4()
            return ('NOT', e)
        elif self.consume('set'):
            v = self.variable()
            self.expect("=")
            t = self.term()
            return ('SET', v, t)
        elif self.peek()[0].isupper():
            # TODO: handle ... & X+Y  (maybe)
            v = self.variable()
            if self.consume(u'←') or self.consume('<-'):
                t = self.term()
            else:
                return ('CALL', ('PRODREF', '$', 'return'), [v], None)
            return ('SET', v, t)
        else:
            # implied return of term
            if self.peek()[0].isupper() or self.peek()[0] == "'":
                t = self.term()
                return ('CALL', ('PRODREF', '$', 'return'), [t], None)
            prodref = self.prodref()
            args = []
            name = prodref[2]
            if prodref[1] == '' and name in self.aliases:
                arity = self.aliases[name][0]
                prodref = self.aliases[name][1]
                i = 0
                args = []
                while i < arity:
                    args.append(self.term())
                    i += 1
            else:
                if self.consume('('):
                    if self.peek() != ')':
                        args.append(self.term())
                        while self.consume(','):
                            args.append(self.term())
                    self.expect(')')
            ibuf = None
            if self.consume('@'):
                ibuf = self.term()
            return ('CALL', prodref, args, ibuf)

    def prodref(self):
        if self.consume('$'):
            self.expect('.')
            name = self.consume_any()
            return ('PRODREF', '$', name)
        else:
            name = self.consume_any()
            return ('PRODREF', '', name)

    def variable(self):
        if self.peek()[0].isupper():
            var = self.consume_any()
            return Variable(var)
        else:
            self.error('variable')

    def term(self):
        lhs = self.term1()
        while self.consume('+'):
            rhs = self.term1()
            lhs = Concat(lhs, rhs)
        return lhs

    def term1(self):
        if self.peek()[0].isupper():
            return self.variable()
        elif (self.peek()[0].isalnum() or
              self.peek()[0] == "'"):
            atom = self.consume_any()
            if atom[0] in ('\'',):
                atom = atom[1:-1]
            subs = []
            if self.consume('('):
                if self.peek() != ')':
                    subs.append(self.term())
                while self.consume(','):
                    subs.append(self.term())
                self.expect(')')
            return Term(atom, subs)
        else:
            self.error('term')
