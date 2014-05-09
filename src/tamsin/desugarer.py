# encoding: UTF-8

# Copyright (c)2014 Chris Pressey, Cat's Eye Technologies.
# Distributed under a BSD-style license; see LICENSE for more information.

from tamsin.ast import (
    Program, Module, Production, ProdBranch,
    And, Or, Not, While, Call, Send, Set,
    Variable, Using, Concat, Fold, Prodref,
    TermNode, VariableNode, AtomNode, ConstructorNode
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
            
            def find_prod_pos(name):
                i = 0
                for prod in prodlist:
                    if prod.name == name:
                        return i
                    i += 1
                return None

            for prod in ast.prodlist:
                prod = self.desugar(prod)
                pos = find_prod_pos(prod.name)
                if pos is None:
                    prodlist.append(prod)
                else:
                    prodlist[pos].branches.extend(prod.branches)
            
            return Module(ast.name, prodlist)
        elif isinstance(ast, Production):
            return Production(ast.name, [self.desugar(x) for x in ast.branches])
        elif isinstance(ast, ProdBranch):
            return ProdBranch(ast.formals, [], self.desugar(ast.body))
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
            under1 = VariableNode('_1')
            under2 = VariableNode('_2')
            set_ = Set(under1, ast.initial)
            send_ = Send(self.desugar(ast.rule), under2)
            acc_ = Set(under1, Concat(under1, under2))
            if ast.constratom is not None:
                assert isinstance(ast.constratom, AtomNode)
                acc_ = Set(under1,
                           ConstructorNode(ast.constratom.text,
                                           [under2, under1]))
            return_ = Call(Prodref('$', 'return'), [under1], None)
            return And(And(set_, While(And(send_, acc_))), return_)
        else:
            raise NotImplementedError(repr(ast))
