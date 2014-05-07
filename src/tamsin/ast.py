# encoding: UTF-8

# Copyright (c)2014 Chris Pressey, Cat's Eye Technologies.
# Distributed under a BSD-style license; see LICENSE for more information.

# Note that __str__ and __repr__ perform very different tasks:
# __str__ : make a string that looks like a Tamsin term (reprify)
# __repr__ : make a string that is valid Python code for constructing the AST

import sys

from tamsin.term import Term, Variable


def format_list(l):
    if len(l) == 0:
        return 'nil'
    else:
        s = l[0]
        if isinstance(l[0], Term):
            s = l[0].repr()
        return 'list(%s, %s)' % (s, format_list(l[1:]))


class AST(object):
    def __unicode__(self):
        raise NotImplementedError(repr(self))


class Program(AST):
    def __init__(self, modmap, modlist):
        self.modmap = modmap
        self.modlist = modlist

    def find_productions(self, prodref):
        mod = prodref.module
        name = prodref.name
        assert mod != ''
        if mod == '$':
            formals = {
                'emit': [Variable('X')],
                'equal': [Variable('L'), Variable('R')],
                'expect': [Variable('X')],
                'fail': [Variable('X')],
                'mkterm': [Variable('T'), Variable('L')],
                'print': [Variable('X')],
                'repr': [Variable('X')],
                'return': [Variable('X')],
                'reverse': [Variable('X'), Variable('E')],
                'startswith': [Variable('X')],
                'unquote': [Variable('X'), Variable('L'), Variable('R')],
            }.get(name, [])
            return [Production('$.%s' % name, 0, formals, [], None)]
        else:
            if mod not in self.modmap:
                raise KeyError("no '%s' module defined" % mod)
            prodmap = self.modmap[mod].prodmap
            if name not in prodmap:
                raise KeyError("no '%s:%s' production defined" % (mod, name))
            return prodmap[name]

    def incorporate(self, other):
        """Add all Modules from other to self.  Changes self.

        """
        assert isinstance(other, Program)

        #print repr(other.modmap.keys())
        #print repr(self.modmap.keys())
        for modname in other.modmap:
            if modname in self.modmap:
                raise KeyError("module '%s' already defined %r %r" %
                    (modname, self.modmap.keys(), other.modmap.keys())
                )
                #print repr((modname, self.modmap.keys(), other.modmap.keys()))
            self.modmap[modname] = other.modmap[modname]
        self.modlist.extend(other.modlist)

    def __repr__(self):
        return "Program(%r, %r)" % (
            self.modmap, self.modlist
        )

    def __str__(self):
        return "program(%s)" % format_list(self.modlist)


class Module(AST):
    def __init__(self, name, prodmap, prodlist):
        self.name = name
        self.prodmap = prodmap
        self.prodlist = prodlist
    
    def __repr__(self):
        return "Module(%r, %r, %r)" % (self.name, self.prodmap, self.prodlist)

    def __str__(self):
        return "module(%s, %s)" % (self.name, format_list(self.prodlist))


class Production(AST):
    def __init__(self, name, rank, formals, locals_, body):
        self.name = name
        self.rank = rank
        self.formals = formals
        self.locals_ = locals_
        self.body = body

    def __repr__(self):
        return u"Production(%r, %r, %r, %r, %r)" % (
            self.name,
            self.rank,
            self.formals,
            self.locals_,
            self.body
        )

    def __str__(self):
        return "production(%s, %s, %s)" % (
            self.name,
            format_list(self.formals),
            self.body
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
            self.module,
            self.name
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
        return u"Set(%r, %r)" % (
            self.variable,
            self.texpr
        )

    def __str__(self):
        return "set(%s, %s)" % (
            self.variable,
            self.texpr
        )


class Concat(AST):
    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs

    def __repr__(self):
        return u"Concat(%r, %r)" % (
            self.lhs,
            self.rhs
        )

    def __str__(self):
        lhs = self.lhs
        if isinstance(lhs, Term):
            lhs = lhs.repr()
        rhs = self.rhs
        if isinstance(rhs, Term):
            rhs = rhs.repr()
        return "%s%s" % (lhs, rhs)


class Using(AST):
    def __init__(self, rule, prodref):
        self.rule = rule
        assert isinstance(prodref, Prodref)
        self.prodref = prodref

    def __repr__(self):
        return u"Using(%r, %r)" % (
            self.rule,
            self.prodref
        )

    def __str__(self):
        return "using(%s, %s)" % (
            self.rule,
            self.prodref
        )


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
            self.initial.repr()
        )
