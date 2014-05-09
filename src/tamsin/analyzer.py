# encoding: UTF-8

# Copyright (c)2014 Chris Pressey, Cat's Eye Technologies.
# Distributed under a BSD-style license; see LICENSE for more information.

from tamsin.ast import (
    Program, Production, Module, And, Or, Not, While, Call, Send, Set,
    Variable, Using, Concat, Prodref, TermNode
)
from tamsin.term import Term, Constructor, Atom
from tamsin.event import EventProducer


class Analyzer(EventProducer):
    """The Analyzer takes a desugared AST, walks it, and returns a new AST.
    It is responsible for:
    
    * Finding the set of local variable names used in each production and
      sticking that in the locals_ field of the new Production node.
    * Resolving any '' modules in Prodrefs to the name of the current
      module.

    * Looking for undefined nonterminals and raising an error if such found.
      (this is done at the end by analyze_prodrefs)

    TODO: it should also find any locals that are accessed before being set
    """
    def __init__(self, program, listeners=None):
        self.listeners = listeners
        self.program = program
        self.current_module = None

    def analyze(self, ast):
        if isinstance(ast, Program):
            modlist = []
            for mod in ast.modlist:
                mod = self.analyze(mod)
                modlist.append(mod)
            self.program = Program(modlist)
            self.analyze_prodrefs(self.program)
            return self.program
        elif isinstance(ast, Module):
            self.current_module = ast
            prodlist = []
            for prod in ast.prodlist:
                prod = self.analyze(prod)
                linked = False
                for parent in prodlist:
                    if parent.name == prod.name:
                        parent.link(prod)
                        linked = True
                        break
                if not linked:
                    prodlist.append(prod)
            self.current_module = None
            return Module(ast.name, prodlist)
        elif isinstance(ast, Production):
            locals_ = set()
            body = self.analyze(ast.body)
            self.collect_locals(body, locals_)
            return Production(ast.name, ast.formals, locals_, body, None)
        elif isinstance(ast, Or):
            return Or(self.analyze(ast.lhs), self.analyze(ast.rhs))
        elif isinstance(ast, And):
            return And(self.analyze(ast.lhs), self.analyze(ast.rhs))
        elif isinstance(ast, Using):
            return Using(self.analyze(ast.rule), self.analyze(ast.prodref))
        elif isinstance(ast, Call):
            return Call(self.analyze(ast.prodref), ast.args, ast.ibuf)
        elif isinstance(ast, Send):
            assert isinstance(ast.variable, TermNode), ast
            assert isinstance(ast.variable.term, Variable), ast
            return Send(self.analyze(ast.rule), ast.variable)
        elif isinstance(ast, Set):
            assert isinstance(ast.variable, TermNode), ast
            assert isinstance(ast.variable.term, Variable), ast
            return Set(ast.variable, self.analyze(ast.texpr))
        elif isinstance(ast, Not):
            return Not(self.analyze(ast.rule))
        elif isinstance(ast, While):
            return While(self.analyze(ast.rule))
        elif isinstance(ast, Concat):
            return Concat(self.analyze(ast.lhs), self.analyze(ast.rhs))
        elif isinstance(ast, TermNode):
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
        elif (isinstance(ast, And) or isinstance(ast, Or) or
              isinstance(ast, Concat)):
            self.collect_locals(ast.lhs, locals_)
            self.collect_locals(ast.rhs, locals_)
        elif isinstance(ast, Using):
            self.collect_locals(ast.rule, locals_)
        elif isinstance(ast, Call):
            pass
        elif isinstance(ast, Send):
            self.collect_locals(ast.variable, locals_)
            self.collect_locals(ast.rule, locals_)
        elif isinstance(ast, Set):
            self.collect_locals(ast.variable, locals_)
            self.collect_locals(ast.texpr, locals_)
        elif isinstance(ast, Not) or isinstance(ast, While):
            self.collect_locals(ast.rule, locals_)
        elif isinstance(ast, TermNode):
            self.collect_locals(ast.term, locals_)
        # terms --- could just call t.collect_variables() and map out names...
        elif isinstance(ast, Variable):
            locals_.add(ast.name)
        elif isinstance(ast, Constructor):
            for sub in ast.contents:
                self.collect_locals(sub, locals_)
        elif isinstance(ast, Atom):
            pass
        else:
            raise NotImplementedError(repr(ast))

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
            module = self.program.find_module(ast.module)
            if not module:
                raise KeyError("no '%s' module defined" % ast.module)
            production = module.find_production(ast.name)
            if not production:
                raise KeyError("no '%s:%s' production defined" %
                    (ast.module, ast.name)
                )
        else:
            raise NotImplementedError(repr(ast))
