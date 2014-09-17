# encoding: UTF-8

# Copyright (c)2014 Chris Pressey, Cat's Eye Technologies.
# Distributed under a BSD-style license; see LICENSE for more information.

from tamsin import ast as a
from tamsin.term import Atom, Constructor, Variable
import tamsin.sysmod


class CodeNode(object):
    def __init__(self, *args, **kwargs):
        self.args = list(args)
        self.kwargs = kwargs

    def append(self, item):
        self.args.append(item)

    def __repr__(self):
        return "%s(%s, %s)" % (
            self.__class__.name,
            ', '.join([repr(a) for a in self.args]),
            ', '.join('%s=%r' % (key, self.kwargs[key]) for key in self.kwargs)
        )


class Program(CodeNode):
    pass


class Prototype(CodeNode):
    pass


class Subroutine(CodeNode):
    pass


class Block(CodeNode):
    pass


class GetVar(CodeNode):
    pass


class Unifier(CodeNode):
    pass


class If(CodeNode):
    pass


class And(CodeNode):
    pass


class Not(CodeNode):
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


class Call(CodeNode):
    pass


class NoMatch(CodeNode):
    pass


class CodeGen(object):
    def __init__(self, program):
        self.program = program

    def generate(self):
        main = self.program.find_production(a.Prodref('main', 'main'))
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
        s = Subroutine(formals)
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

    def gen_no_match(self, module, prod, formals):
        return NoMatch(module, prod, formals)

    def gen_branches(self, module, prod, branches):
        if not branches:
            return Return(NoMatch(module, prod))
        test = Not()
        #for fml_num in xrange(0, len(branch.formals)):
        #    self.emit("    term_match_unifier(%s, i%s, unifier) &&" %
        #        (pat_names[fml_num], fml_num)
        #    )
        branch = branches[0]
        branches = branches[1:]
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
        if isinstance(ast, a.And):
            return Block(
                self.gen_ast(ast.lhs),
                If(GetVar('ok'),
                    self.gen_ast(ast.rhs)
                )
            )
        elif isinstance(ast, a.Or):
            return Block(
                DeclState(),
                SaveState(),
                self.gen_ast(ast.lhs),
                If(Not(GetVar('ok')),
                    Block(
                        RestoreState(),
                        self.gen_asr(ast.rhs)
                    )
                )
            )
        elif isinstance(ast, a.Call):
            prodref = ast.prodref
            prodmod = prodref.module or 'main'
            name = prodref.name
            args = ast.args

            if prodmod == '$':
                argnames = []
                arity = tamsin.sysmod.arity(name)
                for i in xrange(0, arity):
                    argnames.insert(0, self.compile_r(args[i]))

                return Builtin(name, argnames)
            else:
                args = []  # ', '.join([self.compile_r(a) for a in args])
                return Call(prodmod, name, args)
        elif isinstance(ast, a.Send):
            self.compile_r(ast.rule)
            # EMIT PATTERN ... which means generalizing the crap that is
            # currently in the ProdBranch case up there, way up there ^^^
            lname = self.emit_lvalue(ast.variable)
            self.emit("%s = result;" % lname)
        elif isinstance(ast, a.Set):
            self.emit("/* %r */" % ast)
            name = self.compile_r(ast.texpr)
            lname = self.emit_lvalue(ast.variable)
            self.emit("%s = %s;" % (lname, name))
            self.emit("result = %s;" % name)
            self.emit("ok = 1;")
        elif isinstance(ast, a.While):
            return Block(
                DeclareLocal('srname', AtomNode('nil')),
                DeclState(),
                self.compile_r(),
                SetVar('ok', '1'),
                While(GetVar('ok'),
                    Block(
                        SaveState(),
                        self.gen_ast(ast.rule),
                        If(GetVar('ok'),
                            SetVar(srname, 'result')
                        )
                    )
                ),
                RestoreState(),
                SetVar('result', srname),
                SetVar('ok', '1')
            )
        elif isinstance(ast, a.Not):
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
        elif isinstance(ast, Using):
            return Block(
                ScannerPushEngine(ast.prodref.module, ast.prodref.name),
                self.gen_ast(ast.rule),
                ScannerPopEngine(),
            )
        elif isinstance(ast, On):
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
        elif isinstance(ast, Concat):
            name_lhs = self.compile_r(ast.lhs);
            name_rhs = self.compile_r(ast.rhs);
            name = self.new_name()
            self.emit('const struct term *%s = term_concat(term_flatten(%s), term_flatten(%s));' %
                (name, name_lhs, name_rhs)
            )
            return name
        elif isinstance(ast, AtomNode):
            name = self.new_name()
            self.emit('const struct term *%s = term_new_atom("%s", %s);' %
                (name, escaped(ast.text), len(ast.text))
            )
            return name

        elif isinstance(ast, VariableNode):
            name = self.new_name()
            self.emit('const struct term *%s = %s;' %
                (name, ast.name)
            )
            return name
        elif isinstance(ast, PatternVariableNode):
            name = self.new_name()
            self.emit('const struct term *%s = term_new_variable("%s", %s, %s);' %
                 (name, ast.name, len(ast.name), ast.index)
            )
            return name
        elif isinstance(ast, ConstructorNode):
            termlist_name = self.new_name()
            self.emit('struct termlist *%s = NULL;' % termlist_name);
            for c in reversed(ast.contents):
                subname = self.compile_r(c)
                self.emit('termlist_add_term(&%s, %s);' % (termlist_name, subname))
            name = self.new_name()
            self.emit('const struct term *%s = term_new_constructor("%s", %s, %s);' %
                (name, escaped(ast.text), len(ast.text), termlist_name)
            )
            return name
        else:
            raise NotImplementedError(repr(ast))

    def emit_lvalue(self, ast):
        """Does not actually emit anything.  (Yet.)"""
        if isinstance(ast, TermNode):
            return self.emit_lvalue(ast.to_term())
        elif isinstance(ast, Variable):
            return ast.name
        else:
            raise NotImplementedError(repr(ast))
