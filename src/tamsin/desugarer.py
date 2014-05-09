# encoding: UTF-8

# Copyright (c)2014 Chris Pressey, Cat's Eye Technologies.
# Distributed under a BSD-style license; see LICENSE for more information.

from tamsin.ast import (
    Program, Module, Production, And, Or, Not, While, Call, Send, Set,
    Variable, Using, Concat, Fold, Prodref, TermNode
)
from tamsin.term import Term, Atom, Constructor
from tamsin.event import EventProducer


class Desugarer(EventProducer):
    """The Desugarer takes an AST, walks it, and returns a new AST.
    It is responsible for:

    * Desugaring Fold() nodes.
    * Turning the list of Production() nodes into a linked list.

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
            prodlist = []
            for prod in ast.prodlist:
                prod = self.desugar(prod)
                linked = False
                for parent in prodlist:
                    if parent.name == prod.name:
                        parent.link(prod)
                        linked = True
                        break
                if not linked:
                    prodlist.append(prod)
            return Module(ast.name, prodlist)
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
        elif isinstance(ast, TermNode):
            return ast
        elif isinstance(ast, Fold):
            under1 = TermNode(Variable('_1'))
            under2 = TermNode(Variable('_2'))
            set_ = Set(under1, ast.initial)
            send_ = Send(self.desugar(ast.rule), under2)
            acc_ = Set(under1, Concat(under1, under2))
            if ast.constratom is not None:
                assert isinstance(ast.constratom, TermNode)
                assert isinstance(ast.constratom.term, Atom)
                acc_ = Set(under1,
                           TermNode(Constructor(ast.constratom.term.text,
                                    [Variable('_2'), Variable('_1')])))
            return_ = Call(Prodref('$', 'return'), [under1], None)
            return And(And(set_, While(And(send_, acc_))), return_)
        else:
            raise NotImplementedError(repr(ast))
