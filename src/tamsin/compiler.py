# encoding: UTF-8

# Copyright (c)2014 Chris Pressey, Cat's Eye Technologies.
# Distributed under a BSD-style license; see LICENSE for more information.

# Generates a C-language program which, when linked with -ltamsin, has
# the same (we hope) behaviour as interpreting the input Tamsin program.

# Will be DEPRECATED by tamsin.codegen and tamsin.backends.c soon, hopefully.

from tamsin.ast import (
    Production, ProdBranch,
    And, Or, Not, While, Call, Send, Set, Concat, Using, On, Prodref,
    TermNode, AtomNode, VariableNode, PatternVariableNode, ConstructorNode
)
from tamsin.term import Atom, Constructor, Variable
import tamsin.sysmod


PRELUDE = r'''
/*
 * Generated code!  Edit at your own risk!
 * Must be linked with -ltamsin to build.
 */
#include <assert.h>
#include <tamsin.h>

/* global scanner */

struct scanner * scanner;

/* global state: result of last action */

int ok;
const struct term *result;
'''

POSTLUDE = r'''
const struct term *bufterm = NULL;

int read_file(FILE *input) {
    char *buffer = malloc(8193);

    assert(input != NULL);

    while (!feof(input)) {
        int num_read = fread(buffer, 1, 8192, input);
        if (bufterm == NULL) {
            bufterm = term_new_atom(buffer, num_read);
        } else {
            bufterm = term_concat(bufterm, term_new_atom(buffer, num_read));
        }
    }

    free(buffer);
}

int main(int argc, char **argv) {

    if (argc == 1) {
        read_file(stdin);
    } else {
        int i;

        for (i = 1; i < argc; i++) {
            FILE *input = fopen(argv[i], "r");
            read_file(input);
            fclose(input);
        }
    }

    scanner = scanner_new(bufterm->atom, bufterm->size);
    ok = 0;
    result = term_new_atom_from_cstring("nil");

    prod_main_main();

#ifdef HITS_AND_MISSES
    fprintf(stderr, "hits: %d, misses: %d\n", hits, misses);
#endif

    if (ok) {
        term_fput(result, stdout);
        fwrite("\n", 1, 1, stdout);
        exit(0);
    } else {
        term_fput(result, stderr);
        fwrite("\n", 1, 1, stderr);
        exit(1);
    }
}
'''

class Compiler(object):
    def __init__(self, program, outfile):
        self.program = program
        self.outfile = outfile
        self.indent_ = 0
        self.current_prod = None
        self.current_branch = None
        self.currmod = None
        self.name_index = 0

    def new_name(self):
        name = "temp%s" % self.name_index
        self.name_index += 1
        return name

    def indent(self):
        self.indent_ += 1

    def outdent(self):
        self.indent_ -= 1

    def emit(self, *args):
        s = "    " * self.indent_ + ''.join(args) + "\n"
        self.outfile.write(s)

    def compile(self):
        """Returns the name of a local temporary if it created one to
        store its most recent result.  Otherwise returns None.

        """
        self.emit(PRELUDE)

        main = self.program.find_production(Prodref('main', 'main'))
        if not main:
            raise ValueError("no 'main:main' production defined")

        for module in self.program.modlist:
            mod_name = module.name
            for prod in module.prodlist:
                self.emit("void prod_%s_%s(%s);" % (
                    mod_name, prod.name,
                    ', '.join(["const struct term *"
                               for f in prod.branches[0].formals])
                ))
        self.emit("")
        for module in self.program.modlist:
            self.currmod = module
            mod_name = module.name
            for prod in module.prodlist:
                self.current_prod = prod
                self.compile_r(prod)
                self.current_prod = None
            self.currmod = None

        self.emit(POSTLUDE)

    def compile_r(self, ast):
        if isinstance(ast, Production):
            prod = ast
            fmls = []
            i = 0
            for f in prod.branches[0].formals:
                fmls.append("const struct term *i%s" % i)
                i += 1
            fmls = ', '.join(fmls)
            self.emit("void prod_%s_%s(%s) {" % (
                self.currmod.name, prod.name, fmls
             ))
            self.indent()

            for branch in ast.branches:
                self.current_branch = branch
                self.compile_r(branch)
                self.current_branch = None

            self.emit('result = term_new_atom_from_cstring'
                      '("No \'%s\' production matched arguments ");' %
                      self.current_prod.name)
            for i in xrange(0, len(branch.formals)):
                self.emit('result = term_concat(result, term_flatten(i%d));' % i)
                self.emit('result = term_concat(result, term_new_atom_from_cstring(", "));')
            self.emit("ok = 0;")

            self.outdent()
            self.emit("}")
            self.emit("")
        elif isinstance(ast, ProdBranch):
            branch = ast
            all_pattern_variables = []

            self.emit("{")
            self.indent()
            
            pat_names = []
            for fml_num in xrange(0, len(branch.formals)):
                formal = branch.formals[fml_num]
                pat_names.append(self.compile_r(formal))

                variables = []
                formal.collect_variables(variables)
                for variable in variables:
                   if variable not in all_pattern_variables:
                       all_pattern_variables.append(variable)

            self.emit("const struct term *unifier[] = {%s};" %
                ','.join(["NULL"] * len(all_pattern_variables))
            )

            self.emit("if (")

            for fml_num in xrange(0, len(branch.formals)):
                self.emit("    term_match_unifier(%s, i%s, unifier) &&" %
                    (pat_names[fml_num], fml_num)
                )
            self.emit("    1) {")
            self.indent()
            
            # get variables which are found in patterns for this branch
            for var in all_pattern_variables:
                self.emit('const struct term *%s = unifier[%s];' %
                    (var.name, var.index)
                )
                self.emit('assert(%s != NULL);' % var.name);

            all_pattern_variable_names = [x.name for x in all_pattern_variables]
            for local in branch.locals_:
                if local not in all_pattern_variable_names:
                    self.emit("const struct term *%s;" % local)
            self.emit("")

            self.compile_r(branch.body)

            self.emit("return;")
            self.outdent()
            self.emit("}")
            self.outdent()
            self.emit("}")

        elif isinstance(ast, And):
            self.compile_r(ast.lhs)
            self.emit("if (ok) {")
            self.indent()
            self.compile_r(ast.rhs)
            self.outdent()
            self.emit("}")
        elif isinstance(ast, Or):
            self.emit("{")
            self.indent()
            self.emit_decl_state()
            self.emit_save_state()
            self.compile_r(ast.lhs)
            self.emit("if (!ok) {")
            self.indent()
            self.emit_restore_state()
            self.compile_r(ast.rhs)
            self.outdent()
            self.emit("}")
            self.outdent()
            self.emit("}")
        elif isinstance(ast, Call):
            prodref = ast.prodref
            prodmod = prodref.module or 'main'
            name = prodref.name
            args = ast.args

            if prodmod == '$':
                argnames = []
                arity = tamsin.sysmod.arity(name)
                for i in xrange(0, arity):
                    argnames.insert(0, self.compile_r(args[i]))

                if name == 'expect':
                    self.emit('tamsin_expect(scanner, %s);' % argnames[0])
                elif name == 'return':
                    self.emit("result = %s;" % argnames[0])
                    self.emit("ok = 1;")
                elif name == 'fail':
                    self.emit("result = %s;" % argnames[0])
                    self.emit('ok = 0;')
                elif name == 'print':
                    self.emit("result = %s;" % argnames[0])
                    self.emit("term_fput(result, stdout);")
                    self.emit(r'fwrite("\n", 1, 1, stdout);')
                    self.emit("ok = 1;")
                elif name == 'emit':
                    self.emit("result = %s;" % argnames[0])
                    self.emit("term_fput(result, stdout);")
                    self.emit("ok = 1;")
                elif name == 'eof':
                    self.emit('tamsin_eof(scanner);')
                elif name == 'any':
                    self.emit('tamsin_any(scanner);')
                elif name == 'alnum':
                    self.emit('tamsin_alnum(scanner);')
                elif name == 'upper':
                    self.emit('tamsin_upper(scanner);')
                elif name == 'startswith':
                    self.emit('tamsin_startswith(scanner, '
                              'term_flatten(%s)->atom);' % argnames[0])
                elif name == 'unquote':
                    self.emit('result = tamsin_unquote(%s, %s, %s);' %
                        (argnames[2], argnames[1], argnames[0])
                    )
                elif name == 'equal':
                    self.emit('result = tamsin_equal(%s, %s);' %
                        (argnames[1], argnames[0])
                    )
                elif name == 'repr':
                    self.emit('result = tamsin_repr(%s);' % argnames[0])
                    self.emit('ok = 1;')
                elif name == 'reverse':
                    self.emit('result = tamsin_reverse(%s, %s);' %
                        (argnames[1], argnames[0])
                    )
                elif name == 'mkterm':
                    self.emit('result = tamsin_mkterm(%s, %s);' %
                        (argnames[1], argnames[0])
                    )
                    self.emit('ok = 1;')
                elif name == 'gensym':
                    self.emit('result = tamsin_gensym(%s);' % argnames[0])
                    self.emit('ok = 1;')
                elif name == 'hexbyte':
                    self.emit('result = tamsin_hexbyte(%s, %s);' %
                        (argnames[1], argnames[0])
                    )
                    self.emit('ok = 1;')
                elif name == 'format_octal':
                    self.emit('result = tamsin_format_octal(%s);' % argnames[0])
                    self.emit('ok = 1;')
                elif name == 'length':
                    self.emit('result = tamsin_length(%s);' % argnames[0])
                    self.emit('ok = 1;')
                else:
                    raise NotImplementedError(name)
            else:
                args = ', '.join([self.compile_r(a) for a in args])
                self.emit("prod_%s_%s(%s);" % (prodmod, name, args))
        elif isinstance(ast, Send):
            self.compile_r(ast.rule)
            # EMIT PATTERN ... which means generalizing the crap that is
            # currently in the ProdBranch case up there, way up there ^^^
            # *** awfulhak to make compiler fail less ***
            variable = VariableNode(ast.pattern.name)
            lname = self.emit_lvalue(variable)
            self.emit("%s = result;" % lname)
        elif isinstance(ast, Set):
            self.emit("/* %r */" % ast)
            name = self.compile_r(ast.texpr)
            lname = self.emit_lvalue(ast.variable)
            self.emit("%s = %s;" % (lname, name))
            self.emit("result = %s;" % name)
            self.emit("ok = 1;")
        elif isinstance(ast, While):
            self.emit("{")
            self.indent()
            self.emit_decl_state()
            srname = self.compile_r(AtomNode('nil'))
            self.emit("ok = 1;")
            self.emit("while (ok) {")
            self.indent()
            self.emit_save_state()
            self.compile_r(ast.rule)
            self.emit("if (ok) {")
            self.indent()
            self.emit("%s = result;" % srname)
            self.outdent()
            self.emit("}")
            self.outdent()
            self.emit("}") # endwhile
            self.emit_restore_state()
            self.emit("result = %s;" % srname)
            self.emit("ok = 1;")
            self.outdent()
            self.emit("}")
        elif isinstance(ast, Not):
            self.emit("{")
            self.indent()
            self.emit_decl_state()
            self.emit_save_state()
            self.compile_r(ast.rule)
            self.emit_restore_state()
            self.emit("if (ok) {")
            self.indent()
            self.emit("ok = 0;")
            self.emit(r'result = term_new_atom_from_cstring("expected anything else");')
            self.outdent()
            self.emit("} else {")
            self.indent()
            self.emit("ok = 1;")
            self.emit(r'result = term_new_atom_from_cstring("nil");')
            self.outdent()
            self.emit("}")
            self.outdent()
            self.emit("}")
        elif isinstance(ast, Using):
            prodref = ast.prodref
            scanner_mod = prodref.module
            scanner_name = prodref.name
            if scanner_mod == '$':
                if scanner_name == 'utf8':
                    self.emit("scanner_push_engine(scanner, &scanner_utf8_engine);")
                elif scanner_name == 'byte':
                    self.emit("scanner_push_engine(scanner, &scanner_byte_engine);")
            else:
                self.emit("scanner_push_engine(scanner, &prod_%s_%s);" % (
                    scanner_mod, scanner_name
                ))
            self.compile_r(ast.rule)
            self.emit("scanner_pop_engine(scanner);")
        elif isinstance(ast, On):
            self.emit("{")
            self.indent()
            name = self.compile_r(ast.texpr)
            flat_name = self.new_name()
            self.emit("const struct term *%s = term_flatten(%s);" % (flat_name, name))
            self.emit_decl_state()
            self.emit_save_state()
            self.emit("scanner->buffer = %s->atom;" % flat_name);
            self.emit("scanner->size = %s->size;" % flat_name);
            self.emit("scanner->position = 0;");
            self.emit("scanner->reset_position = 0;");
            self.compile_r(ast.rule);
            self.emit_restore_state()
            self.outdent()
            self.emit("}")
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

    def emit_decl_state(self):
        for local in self.current_branch.locals_:
            self.emit("const struct term *save_%s;" % local)
        self.emit("int position;")
        self.emit("int reset_position;")
        self.emit("const char *buffer;")
        self.emit("int buffer_size;")

    def emit_save_state(self):
        for local in self.current_branch.locals_:
            self.emit("save_%s = %s;" % (local, local))
        self.emit("position = scanner->position;")
        self.emit("reset_position = scanner->reset_position;")
        self.emit("buffer = scanner->buffer;")
        self.emit("buffer_size = scanner->size;")

    def emit_restore_state(self):
        self.emit("scanner->position = position;")
        self.emit("scanner->reset_position = reset_position;")
        self.emit("scanner->buffer = buffer;")
        self.emit("scanner->size = buffer_size;")
        for local in self.current_branch.locals_:
            self.emit("%s = save_%s;" % (local, local))


def escaped(s):
    a = ''
    i = 0
    while i < len(s):
        c = s[i]
        # gcc appears to have some issues with \xXX... perhaps it
        # consumes greater or fewer than two hex digits...?
        if ord(c) < 32 or ord(c) > 126:
            a += "\\%03o" % ord(c)
        elif c == "\\":
            a += r"\\"
        elif c == '"':
            a += r'\"'
        else:
            a += c
        i += 1
    return a
