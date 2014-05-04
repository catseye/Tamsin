# encoding: UTF-8

# Copyright (c)2014 Chris Pressey, Cat's Eye Technologies.
# Distributed under a BSD-style license; see LICENSE for more information.

# The AST before the analyzer gets to it is just tuples.

# After the analyzer gets to it, most of the AST is just tuples;
# the exceptions are the two top-level classes.  The interpreter and
# compiler work on these.

from tamsin.term import Variable

class Program(object):
    def __init__(self, prodmap):
        self.prodmap = prodmap

    def find_productions(self, prodref):
        mod = prodref[1]
        name = prodref[2]
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
        return u"Program(%r)" % self.prodmap

class Production(object):
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
