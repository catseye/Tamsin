# encoding: UTF-8

# Copyright (c)2014 Chris Pressey, Cat's Eye Technologies.
# Distributed under a BSD-style license; see LICENSE for more information.

from tamsin import ast as ack
from tamsin.ast import AtomNode, VariableNode
from tamsin.codenode import (
    CodeNode, Program, Prototype, Subroutine,
    Block, If, While, And, Not, Return, Builtin, Call, Truth, Falsity,
    DeclareLocal, GetVar, SetVar, Concat, VariableRef,
    Unifier, PatternMatch, NoMatch,
    DeclState, SaveState, RestoreState,
    MkAtom, MkConstructor,
)
from tamsin.term import Atom, Constructor, Variable
import tamsin.sysmod


# TODO: is this module responsible for allocating names, or is the backend?
# I think it should probably be this module.


class CodeGen(object):
    def __init__(self, program):
        self.program = program
        self.name_index = 0

    def new_name(self):
        name = "temp%s" % self.name_index
        self.name_index += 1
        return name

    def generate(self):
        main = self.program.find_production(ack.Prodref('main', 'main'))
        if not main:
            raise ValueError("no 'main:main' production defined")

        program = Program()
        for module in self.program.modlist:
            for prod in module.prodlist:
                program.append(
                    Prototype(module=module, prod=prod, formals=prod.branches[0].formals)
                )

        for module in self.program.modlist:
            for prod in module.prodlist:
                program.append(
                    self.gen_subroutine(module, prod, prod.branches[0].formals)
                )

        return program

    def gen_subroutine(self, module, prod, formals):
        s = Subroutine(module=module, prod=prod, formals=formals)
        s.append(self.gen_unifier(prod, prod.branches[0]))  # becoming so wrong
        s.append(self.gen_branches(module, prod, prod.branches))            
        return s

    def gen_unifier(self, prod, branch):
        prod.all_pattern_variables = []

        pat_names = []
        for fml_num, formal in enumerate(branch.formals):
            pat_names.append(self.gen_ast(formal))

            variables = []
            formal.collect_variables(variables)
            for variable in variables:
               if variable not in prod.all_pattern_variables:
                   prod.all_pattern_variables.append(variable)

        return Unifier(prod.all_pattern_variables)

    def gen_branches(self, module, prod, branches):
        if not branches:
            return NoMatch(module=module, prod=prod, formals=[])
        branch = branches[0]
        branches = branches[1:]
        test = Truth()
        for fml_num in xrange(0, len(branch.formals)):
            p = PatternMatch()
            #    self.emit("    term_match_unifier(%s, i%s, unifier) &&" %
            #        (pat_names[fml_num], fml_num)
            #    )
            if not test:
                test = p
            else:
                test = And(test, p)
        return If(test,
            self.gen_branch(module, prod, branch),
            self.gen_branches(module, prod, branches)
        )

    def gen_branch(self, module, prod, branch):
        b = Block()

        # get variables which are found in patterns for this branch
        for var in prod.all_pattern_variables:
            #self.emit('const struct term *%s = unifier[%s];' %
            #    (var.name, var.index)
            #)
            #self.emit('assert(%s != NULL);' % var.name);
            b.append(GetMatchedVar(var))
        
        all_pattern_variable_names = [x.name for x in prod.all_pattern_variables]
        for local in branch.locals_:
            if local not in all_pattern_variable_names:
                #self.emit("const struct term *%s;" % local)
                b.append(DeclareLocal(local))

        b.append(self.gen_ast(branch.body))
        return b

    def gen_ast(self, ast):
        if isinstance(ast, ack.And):
            return Block(
                self.gen_ast(ast.lhs),
                If(GetVar('ok'),
                    self.gen_ast(ast.rhs)
                )
            )
        elif isinstance(ast, ack.Or):
            return Block(
                DeclState(),
                SaveState(),
                self.gen_ast(ast.lhs),
                If(Not(GetVar('ok')),
                    Block(
                        RestoreState(),
                        self.gen_ast(ast.rhs)
                    )
                )
            )
        elif isinstance(ast, ack.Call):
            prodref = ast.prodref
            prodmod = prodref.module or 'main'
            name = prodref.name
            args = ast.args
            if prodmod == '$':
                c = Builtin(name=name)
                arity = tamsin.sysmod.arity(name)
                for i in xrange(0, arity):
                    c.append(self.gen_ast(args[i]))
            else:
                c = Call(module=prodmod, name=name)
                for a in args:
                    c.append(self.get_ast(a))
            return c
        elif isinstance(ast, ack.Send):
            return Block(
                self.gen_ast(ast.rule),
                # EMIT PATTERN ... which means generalizing the crap that is
                # currently in the ProdBranch case up there, way up there ^^^
                SetVar(ast.pattern, GetVar('result'))
            )
        elif isinstance(ast, ack.Set):
            return SetVar(ast.variable, self.gen_ast(ast.texpr))
        elif isinstance(ast, ack.While):
            return Block(
                DeclareLocal('srname', MkAtom('nil')),
                DeclState(),
                SetVar(VariableRef('ok'), Truth()),
                While(GetVar('ok'),
                    Block(
                        SaveState(),
                        self.gen_ast(ast.rule),
                        If(GetVar('ok'),
                            SetVar(VariableRef('srname'), GetVar('result'))
                        )
                    )
                ),
                RestoreState(),
                SetVar(VariableRef('result'), GetVar('srname')),
                SetVar(VariableRef('ok'), Truth())
            )
        elif isinstance(ast, ack.Not):
            return Block(
                DeclState(),
                SaveState(),
                self.gen_ast(ast.rule),
                RestoreState(),
                If(GetVar('ok'),
                    Block(
                        SetVar('ok', '0'),
                        self.emit(r'result = term_new_atom_from_cstring("expected anything else");')
                    ), Block(
                        SetVar('ok', '1'),
                        self.emit(r'result = term_new_atom_from_cstring("nil");')
                    )
                )
            )
        elif isinstance(ast, ack.Using):
            return Block(
                ScannerPushEngine(ast.prodref.module, ast.prodref.name),
                self.gen_ast(ast.rule),
                ScannerPopEngine(),
            )
        elif isinstance(ast, ack.On):
            return Block(
                self.gen_ast(ast.texpr),
                #flat_name = self.new_name()
                #self.emit("const struct term *%s = term_flatten(%s);" % (flat_name, name))
                DeclState(),
                SaveState(),
                #self.emit("scanner->buffer = %s->atom;" % flat_name);
                #self.emit("scanner->size = %s->size;" % flat_name);
                #self.emit("scanner->position = 0;");
                #self.emit("scanner->reset_position = 0;");
                self.gen_ast(ast.rule),
                RestoreState()
            )
        elif isinstance(ast, ack.Concat):
            name_lhs = self.gen_ast(ast.lhs)
            name_rhs = self.gen_ast(ast.rhs)
            name = self.new_name()
            return Concat(name_lhs, name_rhs)
        elif isinstance(ast, ack.AtomNode):
            return MkAtom(ast.text)
        elif isinstance(ast, ack.VariableNode):
            return VariableRef(ast.name)
        elif isinstance(ast, ack.PatternVariableNode):
            return VariableRef(ast.name)
        elif isinstance(ast, ack.ConstructorNode):
            return MkConstructor(ast.text)
        else:
            raise NotImplementedError(repr(ast))

    def new_name(self):
        return 'foo'

    def emit_lvalue(self, ast):
        """Does not actually emit anything.  (Yet.)"""
        if isinstance(ast, TermNode):
            return self.emit_lvalue(ast.to_term())
        elif isinstance(ast, Variable):
            return ast.name
        else:
            raise NotImplementedError(repr(ast))
