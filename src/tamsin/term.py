# encoding: UTF-8

# Copyright (c)2014 Chris Pressey, Cat's Eye Technologies.
# Distributed under a BSD-style license; see LICENSE for more information.

class Term(object):
    def __init__(self, name, contents=None):
        self.name = name
        if contents is None:
            contents = []
        self.contents = contents

    def expand(self, context):
        """Expands this term, returning a new term where, for all x, all
        occurrences of (VAR x) are replaced with the value of x in the
        given context.

        """
        return Term(self.name, [x.expand(context) for x in self.contents])

    def __str__(self):
        if not self.contents:
            return self.name
        return "%s(%s)" % (
            self.name, ', '.join([str(x) for x in self.contents])
        )

    def __repr__(self):
        # sigh
        return str(self)


class Variable(Term):
    def __init__(self, name):
        assert name[0].isupper()
        self.name = name
        self.contents = []

    def expand(self, context):
        return context.fetch(self.name)


class Concat(Term):
    def __init__(self, lhs, rhs):
        assert isinstance(lhs, Term)
        assert isinstance(rhs, Term)
        self.lhs = lhs
        self.rhs = rhs

    def expand(self, context):
        lhs = self.lhs.expand(context)
        rhs = self.rhs.expand(context)
        return Term(str(lhs) + str(rhs))

    def __str__(self):
        return "%s + %s" % (self.lhs, self.rhs)
