# encoding: UTF-8

# Copyright (c)2014 Chris Pressey, Cat's Eye Technologies.
# Distributed under a BSD-style license; see LICENSE for more information.

from tamsin.ast import Program, Production
from tamsin.term import Term, Variable
from tamsin.event import EventProducer
from tamsin.scanner import (
    EOF,
    TamsinScannerEngine, CharScannerEngine, ProductionScannerEngine
)


class Analyzer(EventProducer):
    """
    look for undefined nonterminals
    create a map of production name -> list of productions
    create a map of production name -> list of local variables used therein
    """
    def __init__(self, program, listeners=None):
        self.listeners = listeners
        self.program = program
        self.prodmap = {}

    def analyze(self, ast):
        if ast[0] == 'PROGRAM':
            # ('PROGRAM', prodmap, prodlist)
            prodlist = []
            for prod in ast[2]:
                self.prodmap.setdefault(prod[1], []).append(prod)
            for prod in ast[2]:
                prodlist.append(self.analyze(prod))
            # regen prodmap to pick up local variables
            self.prodmap = {}
            for prod in prodlist:
                # todo: also set prod rank here
                self.prodmap.setdefault(prod.name, []).append(prod)
            if 'main' not in self.prodmap:
                raise ValueError("no 'main' production defined")
            return Program(self.prodmap)
        elif ast[0] == 'PROD':
            # ('PROD', name, formals, locals, body)
            locals_ = set()
            self.collect_locals(ast, locals_)
            body = self.analyze(ast[4])
            return Production(ast[1], 0, ast[2], locals_, body)
        elif ast[0] == 'CALL':
            # ('CALL', prodref, args, ibuf)
            prodref = ast[1]
            mod = prodref[1]
            name = prodref[2]
            if mod == '' and name not in self.prodmap:
               raise ValueError("no '%s' production defined" % name)
               # TODO: also check builtins?
            return ('CALL', prodref, ast[2], ast[3])
        elif ast[0] == 'SEND':
            return ('SEND', self.analyze(ast[1]), ast[2])
        elif ast[0] == 'SET':
            return ast
        elif ast[0] == 'AND':
            return ('AND', self.analyze(ast[1]), self.analyze(ast[2]))
        elif ast[0] == 'OR':
            return ('OR', self.analyze(ast[1]), self.analyze(ast[2]))
        elif ast[0] == 'NOT':
            return ('NOT', self.analyze(ast[1]))
        elif ast[0] == 'USING':
            # ('USING', lhs, prodref)
            return ('USING', self.analyze(ast[1]), ast[2])
        elif ast[0] == 'WHILE':
            return ('WHILE', self.analyze(ast[1]))
        else:
            raise NotImplementedError(repr(ast))

    def collect_locals(self, ast, locals_):
        """locals_ should be a set."""

        if ast[0] == 'PROD':
            self.collect_locals(ast[4], locals_)
        if ast[0] == 'SEND':
            locals_.add(ast[2].name)
        elif ast[0] == 'SET':
            locals_.add(ast[1].name)
        elif ast[0] == 'AND':
            self.collect_locals(ast[1], locals_)
            self.collect_locals(ast[2], locals_)
        elif ast[0] == 'OR':
            self.collect_locals(ast[1], locals_)
            self.collect_locals(ast[2], locals_)
        elif ast[0] == 'WHILE':
            self.collect_locals(ast[1], locals_)
