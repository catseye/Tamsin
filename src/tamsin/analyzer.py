# encoding: UTF-8

# Copyright (c)2014 Chris Pressey, Cat's Eye Technologies.
# Distributed under a BSD-style license; see LICENSE for more information.

from tamsin.ast import (
    Program, Production, And, Or, Not, While, Call, Send, Set, Variable, Using,
    Concat, Prodref
)
from tamsin.term import Term, Atom, Constructor
from tamsin.event import EventProducer


class Analyzer(EventProducer):
    """The Analyzer takes a desugared AST, walks it, and returns a new AST.
    It is responsible for:
    
    * Looking for undefined nonterminals and raising an error if such found.
      (this includes 'main')
    * Finding the set of local variable names used in each production and
      sticking that in the locals_ field of the new Production node.
    * Creating a map from production name -> list of productions and
      sticking that in the prodmap field of the new Program node.

    TODO: it should also find any locals that are accessed before being set
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
            return Program(ast.modmap, ast.modlist, self.prodmap, ast.prodlist)
        elif isinstance(ast, Production):
            locals_ = set()
            body = self.analyze(ast.body)
            self.collect_locals(body, locals_)
            return Production(ast.name, 0, ast.formals, locals_, body)
        elif isinstance(ast, Or):
            return Or(self.analyze(ast.lhs), self.analyze(ast.rhs))
        elif isinstance(ast, And):
            return And(self.analyze(ast.lhs), self.analyze(ast.rhs))
        elif isinstance(ast, Using):
            return Using(self.analyze(ast.rule), ast.prodref)
        elif isinstance(ast, Call):
            prodref = ast.prodref
            if prodref.module == '' and prodref.name not in self.prodnames:
               raise ValueError("no '%s' production defined" % prodref.name)
               # TODO: also check builtins?
            return ast
        elif isinstance(ast, Send):
            assert isinstance(ast.variable, Variable), ast
            return Send(self.analyze(ast.rule), ast.variable)
        elif isinstance(ast, Set):
            assert isinstance(ast.variable, Variable), ast
            return Set(ast.variable, self.analyze(ast.texpr))
        elif isinstance(ast, Not):
            return Not(self.analyze(ast.rule))
        elif isinstance(ast, While):
            return While(self.analyze(ast.rule))
        elif isinstance(ast, Concat):
            return Concat(self.analyze(ast.lhs), self.analyze(ast.rhs))
        elif isinstance(ast, Term):
            return ast
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
            self.collect_locals(ast.rule, locals_)
        elif isinstance(ast, Call):
            pass
        elif isinstance(ast, Send):
            self.collect_locals(ast.rule, locals_)
            locals_.add(ast.variable.name)
        elif isinstance(ast, Set):
            locals_.add(ast.variable.name)
        elif isinstance(ast, Not) or isinstance(ast, While):
            self.collect_locals(ast.rule, locals_)
