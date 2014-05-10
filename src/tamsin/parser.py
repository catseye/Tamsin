# encoding: UTF-8

# Copyright (c)2014 Chris Pressey, Cat's Eye Technologies.
# Distributed under a BSD-style license; see LICENSE for more information.

from tamsin.ast import (
    AST, Module, Program, Production, ProdBranch,
    And, Or, Not, While, Call, Prodref,
    Send, Set, Concat, Using, On, Fold,
    AtomNode, VariableNode, ConstructorNode,
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
        prods = []
        main_module = Module('main', prods)
        mods = [main_module]
        while self.peek() is not EOF:
            prod_or_mod = self.prod_or_mod()
            if isinstance(prod_or_mod, Production):
                prods.append(prod_or_mod)
            else:
                mods.append(prod_or_mod)
        if not prods:
            # no main module. kill it.
            mods = mods[1:]
        return Program(mods)

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

    def prod_or_mod(self):
        name = self.consume_any()
        if self.consume("{"):
            prods = []
            while self.peek() is not EOF and self.peek() != "}":
                prods.append(self.production())
            self.expect("}")
            return Module(name, prods)
        else:
            return self.production(name)

    def production(self, name=None):
        if name is None:
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
        for f in formals:
            assert isinstance(f, AST)
        self.expect('=')
        body = self.expr0()
        self.expect('.')
        return Production(name, [ProdBranch(formals, (), body)])

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
        elif self.consume('@'):
            texpr = self.texpr()
            lhs = On(lhs, texpr)
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
            initial = self.texpr()
            constratom = None
            if self.consume('/'):
                constratom = self.term()
            return Fold(lhs, initial, constratom)
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
                Call(Prodref('$', 'return'), [AtomNode('nil')])
            )
        elif self.consume('{'):
            e = self.expr0()
            self.expect('}')
            return While(e)
        elif self.peek()[0] == '"':
            s = self.consume_any()[1:-1]
            return Call(Prodref('$', 'expect'), [AtomNode(s)])
        elif self.consume(u'«') or self.consume('<<'):
            t = self.texpr()
            if self.consume(u'»') or self.consume('>>'):
                return Call(Prodref('$', 'expect'), [t])
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
                return Call(Prodref('$', 'return'), [v])
            return Set(v, t)
        else:
            # implied return of term
            if self.peek()[0].isupper() or self.peek()[0] == "'":
                t = self.texpr()
                return Call(Prodref('$', 'return'), [t])
            prohibit_aliases = False
            if self.peek() == ':':
                # bleah
                prohibit_aliases = True
            prodref = self.prodref()
            args = []
            name = prodref.name
            if not prohibit_aliases and prodref.module == '' and name in self.aliases:
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
            return Call(prodref, args)

    def prodref(self):
        if self.consume('$'):
            module = '$'
            self.expect(':')
            name = self.consume_any()
        elif self.consume(':'):
            module = ''
            name = self.consume_any()
        else:
            module = ''
            name = self.consume_any()
            if self.consume(':'):
                module = name
                name = self.consume_any()
        return Prodref(module, name)

    def variable(self):
        if self.peek()[0].isupper():
            var = self.consume_any()
            return VariableNode(var)
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
                return ConstructorNode(atom, subs)
            else:
                return AtomNode(atom)
        else:
            self.error('term')


# def unescape(s):
#     t = ''
#     i = 0
#     while i < len(s):
#        char = s[i]
#        if char == '\\':
#            i += 1
#            if i == len(s):
#                raise ValueError(s)
#            char = s[i]
#            if char in ESCAPE_SEQUENCE:
#                char = ESCAPE_SEQUENCE[char]
#            elif char == 'x':
#                k = s[i + 1] + s[i + 2]
#                i += 2
#                char = chr(int(k, 16))
#            else:
#                raise ValueError("bad escape")
#        t += char
#        i += 1
#     return t
