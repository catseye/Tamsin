# encoding: UTF-8

# Copyright (c)2014 Chris Pressey, Cat's Eye Technologies.
# Distributed under a BSD-style license; see LICENSE for more information.

from tamsin.ast import (
    Program, Production, Module, And, Or, Not, While, Call, Send, Set,
    Variable, Using, Concat, Prodref
)
from tamsin.term import Term
from tamsin.event import EventProducer


class Analyzer(EventProducer):
    """The Analyzer takes a desugared AST, walks it, and returns a new AST.
    It is responsible for:
    
    * Finding the set of local variable names used in each production and
      sticking that in the locals_ field of the new Production node.
    * Creating a map from module name -> Module and
      sticking that in the modmap field of the Program node.
    * Creating a map from production name -> list of productions and
      sticking that in the prodmap field of the each Module node.
    * Resolving any '' modules in Prodrefs to the name of the current
      module.

    * Looking for undefined nonterminals and raising an error if such found.
      (this is done at the end by analyze_prodrefs)

    TODO: it should also find any locals that are accessed before being set
    """
    def __init__(self, program, listeners=None):
        self.listeners = listeners
        self.program = program
        self.prodnames = set()
        self.modnames = set()
        self.current_module = None

    def analyze(self, ast):
        if isinstance(ast, Program):
            for mod in ast.modlist:
                self.modnames.add(mod.name)
            modmap = {}
            modlist = []
            for mod in ast.modlist:
                mod = self.analyze(mod)
                modlist.append(mod)
                modmap[mod.name] = mod
            self.program = Program(modmap, modlist)
            self.analyze_prodrefs(self.program)
            return self.program
        elif isinstance(ast, Module):
            self.current_module = ast
            for prod in ast.prodlist:
                self.prodnames.add(prod.name)
            prodmap = {}
            prodlist = []
            for prod in ast.prodlist:
                prod = self.analyze(prod)
                prod.rank = len(prodmap.setdefault(prod.name, []))
                prodmap[prod.name].append(prod)
                prodlist.append(prod)
            self.current_module = None
            return Module(ast.name, prodmap, prodlist)
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
            return Using(self.analyze(ast.rule), self.analyze(ast.prodref))
        elif isinstance(ast, Call):
            return Call(self.analyze(ast.prodref), ast.args, ast.ibuf)
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
        elif isinstance(ast, Prodref):
            module = ast.module
            if module == '':
                module = self.current_module.name
            new = Prodref(module, ast.name)
            return new
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

    def analyze_prodrefs(self, ast):
        """does not return anything"""
        if isinstance(ast, Program):
            for mod in ast.modlist:
                self.analyze_prodrefs(mod)
        elif isinstance(ast, Module):
            for prod in ast.prodlist:
                self.analyze_prodrefs(prod)
        elif isinstance(ast, Production):
            self.analyze_prodrefs(ast.body)
        elif isinstance(ast, Or) or isinstance(ast, And):
            self.analyze_prodrefs(ast.lhs)
            self.analyze_prodrefs(ast.rhs)
        elif isinstance(ast, Using):
            self.analyze_prodrefs(ast.rule)
            self.analyze_prodrefs(ast.prodref)
        elif isinstance(ast, Call):
            self.analyze_prodrefs(ast.prodref)
        elif isinstance(ast, Send):
            self.analyze_prodrefs(ast.rule)
        elif isinstance(ast, Set):
            pass
        elif isinstance(ast, Not):
            self.analyze_prodrefs(ast.rule)
        elif isinstance(ast, While):
            self.analyze_prodrefs(ast.rule)
        elif isinstance(ast, Concat):
            pass
        elif isinstance(ast, Term):
            pass
        elif isinstance(ast, Prodref):
            assert ast.module != '', repr(ast)
            if ast.module == '$':
                return # TODO: also check builtins?
            if ast.module not in self.program.modmap:
                raise KeyError("no '%s' module defined" % ast.module)
            module = self.program.modmap[ast.module]
            if ast.name not in module.prodmap:
                raise KeyError("no '%s:%s' production defined" %
                    (ast.module, ast.name)
                )
        else:
            raise NotImplementedError(repr(ast))
