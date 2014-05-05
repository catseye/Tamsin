# encoding: UTF-8

# Copyright (c)2014 Chris Pressey, Cat's Eye Technologies.
# Distributed under a BSD-style license; see LICENSE for more information.

# Note that __unicode__ and __repr__ perform very different tasks:
# __unicode__ : make a string that looks like a Tamsin term
# __repr__ : make a string that is valid Python code for constructing the AST

from tamsin.term import Variable


def format_list(l):
    if len(l) == 0:
        return u'nil'
    else:
        return u'list(%s, %s)' % (l[0], format_list(l[1:]))


class AST(object):
    def __unicode__(self):
        raise NotImplementedError(repr(self))


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
                'expect': [Variable(u'X')],
                'fail': [Variable(u'X')],
                'print': [Variable(u'X')],
                'return': [Variable(u'X')],
                'startswith': [Variable(u'X')],
                'unquote': [Variable(u'X')],
                'mkterm': [Variable(u'T'), Variable(u'L')],
            }.get(name, [])
            return [Production('$.%s' % name, 0, formals, [], None)]
    
    def __repr__(self):
        return u"Program(%r, %r)" % (self.prodmap, self.prodlist)

    def __unicode__(self):
        return u"program(%s)" % format_list(self.prodlist)


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

    def __unicode__(self):
        return u"production(%s, %s, %s)" % (
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

    def __unicode__(self):
        return u"prodref(%s, %s)" % (
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

    def __unicode__(self):
        return u"and(%s, %s)" % (
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

    def __unicode__(self):
        return u"or(%s, %s)" % (
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

    def __unicode__(self):
        return u"not(%s)" % (
            self.rule
        )


class While(AST):
    def __init__(self, rule):
        self.rule = rule

    def __repr__(self):
        return u"While(%r)" % (
            self.rule
        )

    def __unicode__(self):
        return u"while(%s)" % (
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

    def __unicode__(self):        
        return u"call(%s, %s)" % (
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

    def __unicode__(self):
        return u"send(%s, %s)" % (
            self.rule,
            self.variable
        )


class Set(AST):
    def __init__(self, variable, term):
        self.variable = variable
        self.term = term

    def __repr__(self):
        return u"Set(%r, %r)" % (
            self.variable,
            self.term
        )

    def __unicode__(self):
        return u"set(%s, %s)" % (
            self.variable,
            self.term
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

    def __unicode__(self):
        return u"using(%s, %s)" % (
            self.lhs,
            self.prodref
        )
