# encoding: UTF-8

# Copyright (c)2014 Chris Pressey, Cat's Eye Technologies.
# Distributed under a BSD-style license; see LICENSE for more information.

from tamsin.ast import *
from tamsin.event import EventProducer


class Analyzer(EventProducer):
    """
    look for undefined nonterminals
    create a map of production name -> list of productions
    create a map of production name -> list of local variables used therein
    """
    def __init__(self, program, listeners=None):
        self.listeners = listeners
        self.program = program
        self.prodnames = set()
        self.prodmap = {}

    def analyze(self, ast):
        if isinstance(ast, Program):
            for prod in ast.prodlist:
                self.prodnames.add(prod.name)
            for prod in ast.prodlist:
                prod = self.analyze(prod)
                prod.rank = len(self.prodmap.setdefault(prod.name, []))
                self.prodmap[prod.name].append(prod)
            if 'main' not in self.prodmap:
                raise ValueError("no 'main' production defined")
            return Program(self.prodmap, None)
        elif isinstance(ast, Production):
            locals_ = set()
            self.collect_locals(ast, locals_)
            body = self.analyze(ast.body)
            return Production(ast.name, 0, ast.formals, locals_, body)
        elif isinstance(ast, Or):
            return Or(self.analyze(ast.lhs), self.analyze(ast.rhs))
        elif isinstance(ast, And):
            return And(self.analyze(ast.lhs), self.analyze(ast.rhs))
        elif isinstance(ast, Using):
            return Using(self.analyze(ast.lhs), ast.prodref)
        elif isinstance(ast, Call):
            prodref = ast.prodref
            if prodref.module == '' and prodref.name not in self.prodnames:
               raise ValueError("no '%s' production defined" % prodref.name)
               # TODO: also check builtins?
            return ast
        elif isinstance(ast, Send):
            assert isinstance(ast.variable, Variable), ast
            return Send(self.analyze(ast.rule), ast.variable)
        elif ast[0] == 'SET':
            return ast
        elif ast[0] == 'NOT':
            return ('NOT', self.analyze(ast[1]))
        elif ast[0] == 'WHILE':
            return ('WHILE', self.analyze(ast[1]))
        else:
            raise NotImplementedError(repr(ast))

    def collect_locals(self, ast, locals_):
        """locals_ should be a set."""

        if isinstance(ast, Production):
            self.collect_locals(ast.body, locals_)
        elif isinstance(ast, And) or isinstance(ast, Or):
            self.collect_locals(ast.lhs, locals_)
            self.collect_locals(ast.rhs, locals_)
        elif isinstance(ast, Using):
            self.collect_locals(ast.lhs, locals_)
        elif isinstance(ast, Call):
            pass
        elif isinstance(ast, Send):
            locals_.add(ast.variable.name)
        elif ast[0] == 'SET':
            locals_.add(ast[1].name)
        elif ast[0] == 'WHILE':
            self.collect_locals(ast[1], locals_)
        elif ast[0] == 'NOT':
            self.collect_locals(ast[1], locals_)
