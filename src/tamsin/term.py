# encoding: UTF-8

# Copyright (c)2014 Chris Pressey, Cat's Eye Technologies.
# Distributed under a BSD-style license; see LICENSE for more information.

class Term(object):
    def __init__(self, name, contents=None):
        assert isinstance(name, unicode)
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

    def collect_variables(self, variables):
        for x in self.contents:
            x.collect_variables(variables)

    def __unicode__(self):
        if not self.contents:
            return self.name
        return "%s(%s)" % (
            self.name, ', '.join([unicode(x) for x in self.contents])
        )

    def __repr__(self):
        return "Term(%r, %r)" % (self.name, self.contents)


# TODO: this should be a kind of term!
class EOF(Term):
    def __str__(self):
        return "EOF"
    def __repr__(self):
        return "EOF"
EOF = EOF(u'EOF', [])  # unique


class Variable(Term):
    def __init__(self, name):
        assert name[0].isupper()
        self.name = name
        self.contents = []

    def expand(self, context):
        return context.fetch(self.name)

    def collect_variables(self, variables):
        variables.append(self)

    def __unicode__(self):
        return unicode(self.name)

    def __repr__(self):
        return "Variable(%r)" % (self.name)


class Concat(Term):
    def __init__(self, lhs, rhs):
        assert isinstance(lhs, Term)
        assert isinstance(rhs, Term)
        self.lhs = lhs
        self.rhs = rhs

    def expand(self, context):
        lhs = self.lhs.expand(context)
        rhs = self.rhs.expand(context)
        return Term(unicode(lhs) + unicode(rhs))

    def collect_variables(self, variables):
        self.lhs.collect_variables(variables)
        self.rhs.collect_variables(variables)

    def __unicode__(self):
        return u"%s%s" % (self.lhs, self.rhs)

    def __repr__(self):
        return "Concat(%r, %r)" % (self.lhs, self.rhs)
