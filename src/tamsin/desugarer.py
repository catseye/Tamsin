# encoding: UTF-8

# Copyright (c)2014 Chris Pressey, Cat's Eye Technologies.
# Distributed under a BSD-style license; see LICENSE for more information.

from tamsin.ast import (
    Program, Module, Production, And, Or, Not, While, Call, Send, Set,
    Variable, Using, Concat, Fold, Prodref
)
from tamsin.term import Term, Atom, Constructor
from tamsin.event import EventProducer


class Desugarer(EventProducer):
    """The Desugarer takes an AST, walks it, and returns a new AST.
    It is responsible for:

    * Desugaring Fold() nodes.

    """
    def __init__(self, program, listeners=None):
        self.listeners = listeners
        self.program = program

    def desugar(self, ast):
        if isinstance(ast, Program):
            return Program(
                [self.desugar(m) for m in ast.modlist]
            )
        elif isinstance(ast, Module):
            return Module(
                ast.name, [self.desugar(p) for p in ast.prodlist]
            )
        elif isinstance(ast, Production):
            return Production(ast.name, ast.formals, [],
                              self.desugar(ast.body), None)
        elif isinstance(ast, Or):
            return Or(self.desugar(ast.lhs), self.desugar(ast.rhs))
        elif isinstance(ast, And):
            return And(self.desugar(ast.lhs), self.desugar(ast.rhs))
        elif isinstance(ast, Using):
            return Using(self.desugar(ast.rule), ast.prodref)
        elif isinstance(ast, Call):
            return ast
        elif isinstance(ast, Send):
            return Send(self.desugar(ast.rule), ast.variable)
        elif isinstance(ast, Set):
            return Set(ast.variable, self.desugar(ast.texpr))
        elif isinstance(ast, Not):
            return Not(self.desugar(ast.rule))
        elif isinstance(ast, While):
            return While(self.desugar(ast.rule))
        elif isinstance(ast, Concat):
            return Concat(self.desugar(ast.lhs), self.desugar(ast.rhs))
        elif isinstance(ast, Term):
            return ast
        elif isinstance(ast, Fold):
            set_ = Set(Variable('_1'), ast.initial)
            send_ = Send(self.desugar(ast.rule), Variable('_2'))
            acc_ = Set(Variable('_1'), Concat(Variable('_1'), Variable('_2')))
            if ast.constratom is not None:
                assert isinstance(ast.constratom, Atom)
                acc_ = Set(Variable('_1'),
                           Constructor(ast.constratom.text,
                                       [Variable('_2'), Variable('_1')]))
            return_ = Call(Prodref('$', 'return'), [Variable('_1')], None)
            return And(And(set_, While(And(send_, acc_))), return_)
        else:
            raise NotImplementedError(repr(ast))
