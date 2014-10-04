# encoding: UTF-8

# Copyright (c)2014 Chris Pressey, Cat's Eye Technologies.
# Distributed under a BSD-style license; see LICENSE for more information.


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
        return "%s(%s, %s)" % (
            self.__class__.__name__,
            ', '.join([repr(a) for a in self.args]) if self.args else '',
            ', '.join('%s=%r' % (key, self.kwargs[key]) for key in self.kwargs) if self.kwargs else ''
        )


class Program(CodeNode):
    pass


class Prototype(CodeNode):
    pass


class Subroutine(CodeNode):
    pass


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
    pass


class SetVar(CodeNode):
    pass


class Concat(CodeNode):
    pass


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
