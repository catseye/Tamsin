# encoding: UTF-8

# Copyright (c)2014 Chris Pressey, Cat's Eye Technologies.
# Distributed under a BSD-style license; see LICENSE for more information.

# Most of the AST is just tuples; the exceptions are the two top-level
# classes.   (for now, eventally they will all be like this)

from tamsin.term import Variable

class AST(object):
    pass

class Program(AST):
    def __init__(self, prodmap, prodlist):
        self.prodmap = prodmap
        self.prodlist = prodlist

    def find_productions(self, prodref):
        mod = prodref.module
        name = prodref.name
        if mod == '':
            return self.prodmap[name]
        elif mod == '$':
            formals = {
                'expect': [Variable('X')],
                'fail': [Variable('X')],
                'print': [Variable('X')],
                'return': [Variable('X')],
                'startswith': [Variable('X')],
            }.get(name, [])
            return [Production('$.%s' % name, 0, formals, [], None)]
    
    def __repr__(self):
        return u"Program(%r, %r)" % (self.prodmap, self.prodlist)

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
            '...' # self.body
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

class Or(AST):
    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs

    def __repr__(self):
        return u"Or(%r, %r)" % (
            self.lhs,
            self.rhs
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

class Using(AST):
    def __init__(self, lhs, prodref):
        self.lhs = lhs
        assert isinstance(prodref, Prodref)
        self.prodref = prodref

    def __repr__(self):
        return u"Using(%r, %r)" % (
            self.lhs,
            self.prodref
        )
