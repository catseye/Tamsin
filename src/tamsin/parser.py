# encoding: UTF-8

# Copyright (c)2014 Chris Pressey, Cat's Eye Technologies.
# Distributed under a BSD-style license; see LICENSE for more information.

from tamsin.ast import (
    Program, Production, And, Or, Not, While, Call, Send, Set, Concat, Using,
    Prodref
)
from tamsin.term import (
    Atom, Constructor, Variable, EOF
)
from tamsin.event import EventProducer
from tamsin.scanner import (
    Scanner, TamsinScannerEngine
)


class Parser(EventProducer):
    def __init__(self, buffer, scanner_engine=None, listeners=None):
        self.listeners = listeners
        self.scanner = Scanner(buffer, listeners=self.listeners)
        self.scanner.push_engine(scanner_engine or TamsinScannerEngine())
        self.aliases = {
            'eof': (0, Prodref('$', 'eof')),
            'any': (0, Prodref('$', 'any')),
            'print': (1, Prodref('$', 'print')),
            'fail': (1, Prodref('$', 'fail')),
            'return': (1, Prodref('$', 'return')),
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
        return Program({}, prods)

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
        ast = Production(name, 0, formals, (), body)
        return ast

    def expr0(self):
        lhs = self.expr1()
        while self.consume('|') or self.consume('||'):
            rhs = self.expr1()
            lhs = Or(lhs, rhs)
        return lhs

    def expr1(self):
        lhs = self.expr2()
        while self.consume('&') or self.consume('&&'):
            rhs = self.expr2()
            lhs = And(lhs, rhs)
        return lhs

    def expr2(self):
        lhs = self.expr3()
        if self.consume('using'):
            prodref = self.prodref()
            lhs = Using(lhs, prodref)
        return lhs

    def expr3(self):
        lhs = self.expr4()
        if self.consume(u'→') or self.consume('->'):
            v = self.variable()
            lhs = Send(lhs, v)
        return lhs

    def expr4(self):
        lhs = self.expr5()
        if self.consume('/'):
            t = self.term()
            sett = Set(Variable(u'_1'), t)
            sendd = Send(lhs, Variable(u'_2'))
            accc = Set(Variable(u'_1'), Concat(Variable(u'_1'), Variable(u'_2')))
            returnn = Call(Prodref('$', 'return'), [Variable(u'_1')], None)
            lhs = And(And(sett, While(And(sendd, accc))), returnn)
        return lhs

    def expr5(self):
        if self.consume('('):
            e = self.expr0()
            self.expect(')')
            return e
        elif self.consume('['):
            e = self.expr0()
            self.expect(']')
            return Or(e,
                Call(Prodref('$', 'return'), [Atom(u'nil')], None)
            )
        elif self.consume('{'):
            e = self.expr0()
            self.expect('}')
            return While(e)
        elif self.peek()[0] == '"':
            s = unicode(self.consume_any()[1:-1])
            return Call(Prodref('$', 'expect'), [Atom(s)], None)
        elif self.consume(u'«') or self.consume('<<'):
            t = self.texpr()
            if self.consume(u'»') or self.consume('>>'):
                return Call(Prodref('$', 'expect'), [t], None)
            else:
                self.error("'>>'")
        elif self.consume('!'):
            e = self.expr5()
            return Not(e)
        elif self.consume('set'):
            v = self.variable()
            self.expect("=")
            t = self.texpr()
            return Set(v, t)
        elif self.peek()[0].isupper():
            # TODO: handle ... & X+Y  (maybe)
            v = self.variable()
            if self.consume(u'←') or self.consume('<-'):
                t = self.texpr()
            else:
                return Call(Prodref('$', 'return'), [v], None)
            return Set(v, t)
        else:
            # implied return of term
            if self.peek()[0].isupper() or self.peek()[0] == "'":
                t = self.texpr()
                return Call(Prodref('$', 'return'), [t], None)
            prodref = self.prodref()
            args = []
            name = prodref.name
            if prodref.module == '' and name in self.aliases:
                arity = self.aliases[name][0]
                prodref = self.aliases[name][1]
                i = 0
                args = []
                while i < arity:
                    args.append(self.texpr())
                    i += 1
            else:
                if self.consume('('):
                    if self.peek() != ')':
                        args.append(self.texpr())
                        while self.consume(','):
                            args.append(self.texpr())
                    self.expect(')')
            ibuf = None
            if self.consume('@'):
                ibuf = self.texpr()
            return Call(prodref, args, ibuf)

    def prodref(self):
        module = ''
        if self.consume('$'):
            module = '$'
            self.expect(':')
            name = self.consume_any()
        elif self.consume(':'):
            name = self.consume_any()
        else:
            name = self.consume_any()
            if self.consume(':'):
                module = name
                name = self.consume_any()
        return Prodref(module, name)

    def variable(self):
        if self.peek()[0].isupper():
            var = self.consume_any()
            return Variable(var)
        else:
            self.error('variable')

    def texpr(self):
        lhs = self.term()
        while self.consume('+'):
            rhs = self.term()
            lhs = Concat(lhs, rhs)
        return lhs

    def term(self):
        return self.term1()

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
                return Constructor(unicode(atom), subs)
            else:
                return Atom(unicode(atom))
        else:
            self.error('term')
