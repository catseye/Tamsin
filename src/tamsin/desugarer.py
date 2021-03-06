# encoding: UTF-8

# Copyright (c)2014 Chris Pressey, Cat's Eye Technologies.
# Distributed under a BSD-style license; see LICENSE for more information.

from tamsin.ast import (
    Program, Module, Production, ProdBranch,
    And, Or, Not, While, Call, Send, Set,
    Using, On, Concat, Fold, Prodref,
    TermNode, VariableNode, PatternVariableNode, AtomNode, ConstructorNode
)
from tamsin.event import EventProducer


class Desugarer(EventProducer):
    """The Desugarer takes an AST, walks it, and returns a new AST.
    It is responsible for:

    * Desugaring Fold() nodes.
    * Turning the list of Production() nodes into a linked list.
    * Turning VariableNode() nodes into PatternVariableNodes in a pattern.

    """
    def __init__(self, program, listeners=None):
        self.listeners = listeners
        self.program = program
        self.pattern = False
        self.index = 0

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
            self.pattern = True
            self.index = 0
            formals = [self.desugar(f) for f in ast.formals]
            self.pattern = False
            return ProdBranch(formals, [], self.desugar(ast.body))
        elif isinstance(ast, Or):
            return Or(self.desugar(ast.lhs), self.desugar(ast.rhs))
        elif isinstance(ast, And):
            return And(self.desugar(ast.lhs), self.desugar(ast.rhs))
        elif isinstance(ast, Using):
            return Using(self.desugar(ast.rule), ast.prodref)
        elif isinstance(ast, On):
            return On(self.desugar(ast.rule), self.desugar(ast.texpr))
        elif isinstance(ast, Call):
            return ast
        elif isinstance(ast, Send):
            self.pattern = True
            pattern = self.desugar(ast.pattern)
            self.pattern = False
            return Send(self.desugar(ast.rule), pattern)
        elif isinstance(ast, Set):
            return Set(ast.variable, self.desugar(ast.texpr))
        elif isinstance(ast, Not):
            return Not(self.desugar(ast.rule))
        elif isinstance(ast, While):
            return While(self.desugar(ast.rule))
        elif isinstance(ast, Concat):
            return Concat(self.desugar(ast.lhs), self.desugar(ast.rhs))
        elif isinstance(ast, AtomNode):
            return ast
        elif isinstance(ast, ConstructorNode):
            return ConstructorNode(ast.text,
                                   [self.desugar(x) for x in ast.contents])
        elif isinstance(ast, VariableNode):
            if self.pattern:
                index = self.index
                self.index += 1
                return PatternVariableNode(ast.name, index)
            return ast
        elif isinstance(ast, Fold):
            under1 = VariableNode('_1')
            under2 = VariableNode('_2')
            set_ = Set(under1, ast.initial)
            send_ = Send(self.desugar(ast.rule), under2)
            acc_ = Set(under1, Concat(under1, under2))
            if ast.tag is not None:
                assert isinstance(ast.tag, AtomNode)
                acc_ = Set(under1,
                           ConstructorNode(ast.tag.text,
                                           [under2, under1]))
            return_ = Call(Prodref('$', 'return'), [under1])
            return And(And(set_, While(And(send_, acc_))), return_)
        else:
            raise NotImplementedError(repr(ast))
