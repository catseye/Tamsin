# encoding: UTF-8

# Copyright (c)2014 Chris Pressey, Cat's Eye Technologies.
# Distributed under a BSD-style license; see LICENSE for more information.

# Note that __str__ and __repr__ and repr perform very different tasks:
# __str__ : flattening operation on Tamsin terms
# repr: reprifying operation on Tamsin terms
# __repr__ : make a string that is valid Python code for constructing the Term


BAREWORD = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz'
PRINTABLE = (' !"#$%&()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[]^_'
             '`abcdefghijklmnopqrstuvwxyz{|}~')


def repr_escape(t):
    if len(t) == 0:
        return "''"
    if all(c in BAREWORD for c in t):
        return t
    s = ''
    for c in t:
        if c == "'":
            s += r"\'"
        elif c == "\\":
            s += r"\\"
        elif ord(c) > 31 and ord(c) < 127:
            s += c
        else:
            s += r"\x%02x" % ord(c)
    return "'%s'" % s


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

    def repr(self):
        raise NotImplementedError

    @classmethod
    def match_all(_class, patterns, values):
        """Returns a dict of bindings if all values match all patterns,
        or False if there was a mismatch.

        """
        i = 0
        bindings = {}
        while i < len(patterns):
            sub = patterns[i].match(values[i])
            if sub == False:
                return False
            bindings.update(sub)
            i += 1
        return bindings

    def match(self, value):
        raise NotImplementedError
        

class EOF(Term):
    def __str__(self):
        return "EOF"

    def __repr__(self):
        return "EOF"

    def repr(self):
        return str(self)

    def match(self, value):
        return {} if value is self else False


EOF = EOF()  # unique


class Atom(Term):
    def __init__(self, text):
        assert not isinstance(text, unicode)
        self.text = text

    def __str__(self):
        return self.text

    def __repr__(self):
        return "Atom(%r)" % (self.text)

    def repr(self):
        return repr_escape(self.text)

    def match(self, value):
        if not isinstance(value, Atom):
            return False
        if self.text == value.text:
            return {}
        else:
            return False

    def reversed(self, sentinel):
        if self.match(sentinel) != False:
            return self
        raise ValueError("malformed list")


class Constructor(Term):
    def __init__(self, tag, contents):
        assert not isinstance(tag, unicode)
        self.tag = tag
        for c in contents:
            assert isinstance(c, Term), repr(c)
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

    def repr(self):
        return "%s(%s)" % (
            repr_escape(self.tag), ', '.join([x.repr() for x in self.contents])
        )

    def match(self, value):
        if not isinstance(value, Constructor):
            return False
        if self.tag != value.tag:
            return False
        if len(self.contents) != len(value.contents):
            return False
        bindings = {}
        i = 0
        while i < len(self.contents):
            b = self.contents[i].match(value.contents[i])
            if b == False:
                return False
            bindings.update(b)
            i += 1
        return bindings

    def reversed(self, sentinel):
        acc = sentinel
        l = self
        tag = self.tag
        while isinstance(l, Constructor) and l.tag == tag:
            acc = Constructor(tag, [l.contents[0], acc])
            if len(l.contents) < 2:
                break
            l = l.contents[1]
        if l.match(sentinel) == False:
            raise ValueError("malformed list %s" % l.repr())
        return acc


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

    def repr(self):
        return self.name

    def match(self, value):
        return {self.name: value}
