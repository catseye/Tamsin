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
    def __init__(self, program, listeners=None):
        self.listeners = listeners
        self.program = program

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
                self.analyze(prod)
            mains = self.find_productions(('PRODREF', '', 'main'))
            if not mains:
                raise ValueError("no 'main' production defined")
        elif ast[0] == 'PROD':
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
