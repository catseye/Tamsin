# encoding: UTF-8

# Copyright (c)2014 Chris Pressey, Cat's Eye Technologies.
# Distributed under a BSD-style license; see LICENSE for more information.


# TODO: some of these are definitely hierarchical, and some are definitely
# not.  make the distinction.  make the latter more like 3-address-code.


class CodeNode(object):
    def __init__(self, *args, **kwargs):
        self.args = list(args)
        self.kwargs = kwargs

    def append(self, item):
        self.args.append(item)

    def __getitem__(self, key):
        if key in self.kwargs:
            return self.kwargs[key]
        return self.args[key]

    def __repr__(self):
        return "%s(%s%s)" % (
            self.__class__.__name__,
            (', '.join([repr(a) for a in self.args]) + ', ') if self.args else '',
            ', '.join('%s=%r' % (key, self.kwargs[key]) for key in self.kwargs) if self.kwargs else ''
        )


class Program(CodeNode):
    """Represents a target program."""
    pass


class Prototype(CodeNode):
    """Represents a prototype for a subroutine in a target program."""
    pass


class Subroutine(CodeNode):
    """Represents a subroutine in a target program."""
    def __init__(self, module, prod, formals, children):
        self.module = module
        self.prod = prod
        self.formals = formals
        self.children = children

    def __repr__(self):
        return "Subroutine(%r, %r, %r, %r)" % (
            self.module, self.prod, self.formals, self.children
        )


class Block(CodeNode):
    pass


class If(CodeNode):
    pass


class While(CodeNode):
    pass


class And(CodeNode):
    pass


class Not(CodeNode):
    pass


class DeclareLocal(CodeNode):
    pass


class GetVar(CodeNode):
    """name is the name of the target-language variable."""
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "GetVar(%r)" % (self.name)


class SetVar(CodeNode):
    """ref is a VariableRef for the target-language variable.
    expr is an expression."""
    def __init__(self, ref, expr):
        self.ref = ref
        self.expr = expr

    def __repr__(self):
        return "SetVar(%r, %r)" % (self.ref, self.expr)


class Concat(CodeNode):
    def __init__(self, name, lhs, rhs):
        self.name = name
        self.lhs = lhs
        self.rhs = rhs

    def __repr__(self):
        return "Concat(%r, %r, %r)" % (self.name, self.lhs, self.rhs)


class Unifier(CodeNode):
    pass


class PatternMatch(CodeNode):
    pass


class Return(CodeNode):
    pass


class DeclState(CodeNode):
    pass


class SaveState(CodeNode):
    pass


class RestoreState(CodeNode):
    pass


class Builtin(CodeNode):
    pass


class Call(CodeNode):
    pass


class NoMatch(CodeNode):
    pass


class Truth(CodeNode):
    pass


class Falsity(CodeNode):
    pass


class VariableRef(CodeNode):
    pass


class MkAtom(CodeNode):
    pass


class MkConstructor(CodeNode):
    """Represents some code in the target program to make a constructor."""
    def __init__(self, text, children):
        self.text = text
        self.children = children

    def __repr__(self):
        return "MkConstructor(%r, %r)" % (
            self.text, self.children
        )

class ScannerPushEngine(CodeNode):
    pass


class ScannerPopEngine(CodeNode):
    pass


class GetMatchedVar(CodeNode):
    pass
