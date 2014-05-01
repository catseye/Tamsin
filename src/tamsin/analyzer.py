# encoding: UTF-8

# Copyright (c)2014 Chris Pressey, Cat's Eye Technologies.
# Distributed under a BSD-style license; see LICENSE for more information.

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
        self.localsmap = {}  # TODO: not great, does not handle multibody prods

    # TODO: inherit from ProgramProcessor
    def find_productions(self, prodref):
        mod = prodref[1]
        name = prodref[2]
        prods = []
        if mod == '':
            for prod in self.program[2]:
                if prod[1] == name:
                    prods.append(prod)
        return prods

    def analyze(self, ast):
        self.event('interpret_ast', ast)
        if ast[0] == 'PROGRAM':
            for prod in ast[2]:
                self.prodmap.setdefault(prod[1], []).append(prod)
                self.analyze(prod)
            mains = self.find_productions(('PRODREF', '', 'main'))
            if not mains:
                raise ValueError("no 'main' production defined")
        elif ast[0] == 'PROD':
            self.collect_locals(ast, self.localsmap.setdefault(ast[1], set()))
            self.analyze(ast[3])
        elif ast[0] == 'CALL':
            prodref = ast[1]
            name = prodref[2]
            if prodref[1] == '':
               prods = self.find_productions(prodref)
               if not prods:
                   raise ValueError("no '%s' production defined" % name)
               # TODO: also check builtins?
        elif ast[0] == 'SEND':
            self.analyze(ast[1])
        elif ast[0] == 'SET':
            pass
        elif ast[0] == 'AND':
            self.analyze(ast[1])
            self.analyze(ast[2])
        elif ast[0] == 'OR':
            self.analyze(ast[1])
            self.analyze(ast[2])
        elif ast[0] == 'NOT':
            self.analyze(ast[1])
        elif ast[0] == 'USING':
            self.analyze(ast[1])
        elif ast[0] == 'WHILE':
            self.analyze(ast[1])
        else:
            raise NotImplementedError(repr(ast))

    def collect_locals(self, ast, locals_):
        """locals_ should be a set."""

        if ast[0] == 'PROD':
            self.collect_locals(ast[3], locals_)
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
