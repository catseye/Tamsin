# encoding: UTF-8

# Copyright (c)2014 Chris Pressey, Cat's Eye Technologies.
# Distributed under a BSD-style license; see LICENSE for more information.

# Note that __str__ and __repr__ perform very different tasks:
# __str__ : make a string that looks like a Tamsin term
# __repr__ : make a string that is valid Python code for constructing the Term


class Term(object):
    def expand(self, context):
        """Expands this term, returning a new term where, for all x, all
        occurrences of (VAR x) are replaced with the value of x in the
        given context.

        """
        return self

    def collect_variables(self, variables):
        pass

    def __str__(self):
        raise NotImplementedError

    def __repr__(self):
        raise NotImplementedError


class EOF(Term):
    def __str__(self):
        return "EOF"

    def __repr__(self):
        return "EOF"

EOF = EOF()  # unique


class Atom(Term):
    def __init__(self, text):
        assert not isinstance(text, unicode)
        self.text = text

    def __str__(self):
        return self.text

    def __repr__(self):
        return "Atom(%r)" % (self.text)


class Constructor(Term):
    def __init__(self, tag, contents):
        assert not isinstance(tag, unicode)
        self.tag = tag
        self.contents = contents

    def expand(self, context):
        return Constructor(self.tag, [x.expand(context) for x in self.contents])

    def collect_variables(self, variables):
        for x in self.contents:
            x.collect_variables(variables)

    def __str__(self):
        return "%s(%s)" % (
            self.tag, ', '.join([str(x) for x in self.contents])
        )

    def __repr__(self):
        return "Constructor(%r, %r)" % (self.tag, self.contents)


class Variable(Term):
    def __init__(self, name):
        assert not isinstance(name, unicode)
        assert name[0].isupper() or name[0] == u'_', name
        self.name = name

    def expand(self, context):
        return context.fetch(self.name)

    def collect_variables(self, variables):
        variables.append(self)

    def __str__(self):
        return self.name

    def __repr__(self):
        return "Variable(%r)" % (self.name)
