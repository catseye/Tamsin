# encoding: UTF-8

# Copyright (c)2014 Chris Pressey, Cat's Eye Technologies.
# Distributed under a BSD-style license; see LICENSE for more information.

# Note that __str__ and __repr__ perform very different tasks:
# __str__ : make a string that looks like a Tamsin term (reprify)
# __repr__ : make a string that is valid Python code for constructing the AST

import sys

from tamsin.term import Term, Atom, Variable, Constructor


def format_list(l):
    if len(l) == 0:
        return 'nil'
    else:
        return 'list(%s, %s)' % (l[0], format_list(l[1:]))


class AST(object):
    def __unicode__(self):
        raise NotImplementedError(repr(self))


class Program(AST):
    def __init__(self, modlist):
        self.modlist = modlist

    def find_module(self, name):
        for m in self.modlist:
            if m.name == name:
                return m
        return None

    def find_production(self, prodref):
        module_name = prodref.module
        prod_name = prodref.name
        assert module_name != ''
        if module_name == '$':
            formals = {
                'emit': [VariableNode('X')],
                'equal': [VariableNode('L'), VariableNode('R')],
                'expect': [VariableNode('X')],
                'fail': [VariableNode('X')],
                'mkterm': [VariableNode('T'), VariableNode('L')],
                'print': [VariableNode('X')],
                'repr': [VariableNode('X')],
                'return': [VariableNode('X')],
                'reverse': [VariableNode('X'), VariableNode('E')],
                'startswith': [VariableNode('X')],
                'unquote': [VariableNode('X'), VariableNode('L'), VariableNode('R')],
            }.get(prod_name, [])
            return Production('$.' + prod_name, [ProdBranch(formals, [], None)])
        else:
            module = self.find_module(module_name)
            if not module:
                raise KeyError("no '%s' module defined" % module_name)
            production = module.find_production(prod_name)
            if not production:
                raise KeyError("no '%s:%s' production defined" %
                    (module_name, prod_name)
                )
            return production

    def incorporate(self, other):
        """Add all Modules from other to self.  Changes self.

        """
        assert isinstance(other, Program)

        for module in other.modlist:
            modname = module.name
            if self.find_module(modname):
                raise KeyError("module '%s' already defined" % modname)
            self.modlist.append(module)

    def __repr__(self):
        return "Program(%r)" % self.modlist

    def __str__(self):
        return "program(%s)" % format_list(self.modlist)


class Module(AST):
    def __init__(self, name, prodlist):
        self.name = name
        self.prodlist = prodlist

    def find_production(self, name):
        prods = []
        for prod in self.prodlist:
            if prod.name == name:
                prods.append(prod)
        assert len(prods) in (0, 1), repr((name, prods))
        if not prods:
            return None
        return prods[0]

    def __repr__(self):
        return "Module(%r, %r)" % (self.name, self.prodlist)

    def __str__(self):
        return "module(%s, %s)" % (self.name, format_list(self.prodlist))


class Production(AST):
    def __init__(self, name, branches):
        self.name = name
        self.branches = branches

    def link(self, other):
        if self.next is None:
            self.next = other
        else:
            self.next.link(other)

    def __repr__(self):
        return "Production(%r, %r)" % (
            self.name,
            self.branches,
        )

    def __str__(self):
        return "production(%s, %s)" % (
            self.name,
            format_list(self.branches),
        )


class ProdBranch(AST):
    def __init__(self, formals, locals_, body):
        self.formals = formals
        self.locals_ = locals_
        self.body = body

    def __repr__(self):
        return u"Prodbranch(%r, %r, %r)" % (
            self.formals,
            self.locals_,
            self.body,
        )

    def __str__(self):
        return "prodbranch(%s, %s, %s)" % (
            format_list(self.formals),
            format_list(self.locals_),
            self.body,
        )


class Prodref(AST):
    def __init__(self, module, name):
        self.module = module
        self.name = name

    def __repr__(self):
        return u"Prodref(%r, %r)" % (
            self.module,
            self.name
        )

    def __str__(self):
        return "prodref(%s, %s)" % (
            Atom(self.module).repr(),
            Atom(self.name).repr()
        )


class And(AST):
    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs

    def __repr__(self):
        return u"And(%r, %r)" % (
            self.lhs,
            self.rhs
        )

    def __str__(self):
        return "and(%s, %s)" % (
            self.lhs,
            self.rhs
        )


class Or(AST):
    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs

    def __repr__(self):
        return u"Or(%r, %r)" % (
            self.lhs,
            self.rhs
        )

    def __str__(self):
        return "or(%s, %s)" % (
            self.lhs,
            self.rhs
        )


class Not(AST):
    def __init__(self, rule):
        self.rule = rule

    def __repr__(self):
        return u"Not(%r)" % (
            self.rule
        )

    def __str__(self):
        return "not(%s)" % (
            self.rule
        )


class While(AST):
    def __init__(self, rule):
        self.rule = rule

    def __repr__(self):
        return u"While(%r)" % (
            self.rule
        )

    def __str__(self):
        return "while(%s)" % (
            self.rule
        )


class Call(AST):
    def __init__(self, prodref, args, ibuf):
        self.prodref = prodref
        for a in args:
            assert isinstance(a, AST)
        self.args = args
        self.ibuf = ibuf

    def __repr__(self):
        return u"Call(%r, %r, %r)" % (
            self.prodref,
            self.args,
            self.ibuf
        )

    def __str__(self):        
        return "call(%s, %s)" % (
            self.prodref,
            format_list(self.args)
        )


class Send(AST):
    def __init__(self, rule, variable):
        self.rule = rule
        self.variable = variable

    def __repr__(self):
        return u"Send(%r, %r)" % (
            self.rule,
            self.variable
        )

    def __str__(self):
        return "send(%s, %s)" % (
            self.rule,
            self.variable
        )


class Set(AST):
    def __init__(self, variable, texpr):
        self.variable = variable
        self.texpr = texpr

    def __repr__(self):
        return u"Set(%r, %r)" % (self.variable, self.texpr)

    def __str__(self):
        return "set(%s, %s)" % (self.variable, self.texpr)


class Concat(AST):
    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs

    def __repr__(self):
        return u"Concat(%r, %r)" % (self.lhs, self.rhs)

    def __str__(self):
        return "concat(%s, %s)" % (self.lhs, self.rhs)


class Using(AST):
    def __init__(self, rule, prodref):
        self.rule = rule
        assert isinstance(prodref, Prodref)
        self.prodref = prodref

    def __repr__(self):
        return u"Using(%r, %r)" % (self.rule, self.prodref)

    def __str__(self):
        return "using(%s, %s)" % (self.rule, self.prodref)


class Fold(AST):
    def __init__(self, rule, initial, constratom):
        self.rule = rule
        self.initial = initial
        self.constratom = constratom

    def __repr__(self):
        return u"Fold(%r, %r, %r)" % (
            self.rule,
            self.initial,
            self.constratum
        )

    def __str__(self):
        return "fold(%s, %s)" % (
            self.rule,
            self.initial
        )


class TermNode(AST):
    def __init__(self, *args):
        raise NotImplementedError("abstract class!")

    def to_term(self):
        raise NotImplementedError


class AtomNode(TermNode):
    def __init__(self, text):
        self.text = text

    def __repr__(self):
        return u"AtomNode(%r)" % self.text

    def __str__(self):
        return "atom(%s)" % Atom(self.text).repr()

    def to_term(self):
        return Atom(self.text)


class VariableNode(TermNode):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return u"VariableNode(%r)" % self.name

    def __str__(self):
        return "variable(%s)" % Atom(self.name).repr()

    def to_term(self):
        return Variable(self.name)


class ConstructorNode(TermNode):
    def __init__(self, text, contents):
        self.text = text
        self.contents = contents
        for c in self.contents:
            assert isinstance(c, TermNode)

    def __repr__(self):
        return u"ConstructorNode(%r, %r)" % (self.text, self.contents)

    def __str__(self):
        return "constructor(%s, %s)" % (
            Atom(self.text).repr(),
            format_list(self.contents)
        )

    def to_term(self):
        return Constructor(self.text, [
            x.to_term() for x in self.contents
        ])
