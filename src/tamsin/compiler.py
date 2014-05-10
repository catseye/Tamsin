# encoding: UTF-8

# Copyright (c)2014 Chris Pressey, Cat's Eye Technologies.
# Distributed under a BSD-style license; see LICENSE for more information.

# Generates a C-language program which, when linked with -ltamsin, has
# the same (we hope) behaviour as interpreting the input Tamsin program.
# Does not support `using` or `@` at the moment.

from tamsin.ast import (
    Production, ProdBranch,
    And, Or, Not, While, Call, Send, Set, Concat, Using, Prodref,
    TermNode, VariableNode
)
from tamsin.term import Atom, Constructor, Variable

PRELUDE = r'''
/*
 * Generated code!  Edit at your own risk!
 * Must be linked with -ltamsin to build.
 */
#include <tamsin.h>

/* global scanner */

struct scanner * scanner;

/* global state: result of last action */

int ok;
struct term *result;
'''

POSTLUDE = r'''
int main(int argc, char **argv) {
    FILE *input = NULL;
    char *filename = argv[1];
    char *buffer = malloc(8193);
    struct term *bufterm = NULL;

    if (filename == NULL) {
        input = stdin;
    } else {
        input = fopen(filename, "r");
    }

    assert(input != NULL);
    while (!feof(input)) {
        int num_read = fread(buffer, 1, 8192, input);
        if (bufterm == NULL) {
            bufterm = term_new(buffer, num_read);
        } else {
            bufterm = term_concat(bufterm, term_new(buffer, num_read));
        }
    }

    scanner = scanner_new(bufterm->atom, bufterm->size);
    ok = 0;
    result = term_new_from_cstring("nil");

    prod_main_main();

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
                    ', '.join(["struct term *" % f for f in prod.branches[0].formals])
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
                fmls.append("struct term *i%s" % i)
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
            
            # ... ???
            
            self.emit('result = term_new_from_cstring'
                      '("No \'%s\' production matched arguments ");' %
                      self.current_prod.name)
            for i in xrange(0, len(branch.formals)):
                self.emit('result = term_concat(result, term_flatten(i%d));' % i)
                self.emit('result = term_concat(result, term_new_from_cstring(", "));')
            self.emit("ok = 0;")

            self.outdent()
            self.emit("}")
            self.emit("")
        elif isinstance(ast, ProdBranch):
            branch = ast
            all_pattern_variables = set()

            self.emit("{")
            self.indent()
            
            for fml_num in xrange(0, len(branch.formals)):
                self.emit_term(branch.formals[fml_num].to_term(),
                               "pattern%s" % fml_num, pattern=True)
            
            self.emit("if (")
            
            for fml_num in xrange(0, len(branch.formals)):
                self.emit("    term_match(pattern%s, i%s) &&" %
                    (fml_num, fml_num)
                )
            self.emit("    1) {")
            self.indent()
            
            # declare and get variables which are found in patterns for this branch
            for fml_num in xrange(0, len(branch.formals)):
                variables = []
                formal = branch.formals[fml_num]
                formal.to_term().collect_variables(variables)
                for variable in variables:
                    self.emit('struct term *%s = '
                              'term_find_variable(pattern%s, "%s");' %
                        (variable.name, fml_num, variable.name)
                    )
                    all_pattern_variables.add(variable.name)
            
            for local in branch.locals_:
                if local not in all_pattern_variables:
                    self.emit("struct term *%s;" % local)
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
                if name == 'expect':
                    self.emit_term(args[0].to_term(), "temp")
                    self.emit('tamsin_expect(scanner, temp);')
                elif name == 'return':
                    # TODO: make 'em all like this!
                    name = self.compile_r(args[0])
                    self.emit("result = %s;" % name)
                    self.emit("ok = 1;")
                elif name == 'print':
                    self.emit_term(args[0].to_term(), "temp")
                    self.emit("result = temp;")
                    self.emit("term_fput(result, stdout);")
                    self.emit(r'fwrite("\n", 1, 1, stdout);')
                    self.emit("ok = 1;")
                elif name == 'emit':
                    self.emit_term(args[0].to_term(), "temp")
                    self.emit("result = temp;")
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
                    self.emit_term(args[0].to_term(), "temp")
                    self.emit('tamsin_startswith(scanner, term_flatten(temp)->atom);')
                elif name == 'unquote':
                    self.emit_term(args[0].to_term(), "temp")
                    self.emit_term(args[1].to_term(), "lquote")
                    self.emit_term(args[2].to_term(), "rquote")
                    self.emit('result = tamsin_unquote(temp, lquote, rquote);')
                elif name == 'equal':
                    self.emit_term(args[0].to_term(), "templ")
                    self.emit_term(args[1].to_term(), "tempr")
                    self.emit('result = tamsin_equal(templ, tempr);')
                elif name == 'repr':
                    self.emit_term(args[0].to_term(), "temp")
                    self.emit('result = term_repr(temp);')
                    self.emit('ok = 1;')
                elif name == 'reverse':
                    self.emit_term(args[0].to_term(), "templist")
                    self.emit_term(args[1].to_term(), "tempsentinel")
                    self.emit('result = tamsin_reverse(templist, tempsentinel);')
                elif name == 'mkterm':
                    self.emit_term(args[0].to_term(), "temp_atom")
                    self.emit_term(args[1].to_term(), "temp_list")
                    self.emit('result = tamsin_mkterm(temp_atom, temp_list);')
                    self.emit('ok = 1;')
                elif name == 'fail':
                    name = self.compile_r(args[0])
                    self.emit("result = %s;" % name)
                    self.emit('ok = 0;')
                else:
                    raise NotImplementedError(name)
            else:
                args = ', '.join([self.compile_r(a) for a in args])
                self.emit("prod_%s_%s(%s);" % (prodmod, name, args))
        elif isinstance(ast, Send):
            self.compile_r(ast.rule)
            lname = self.emit_lvalue(ast.variable)
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
            self.emit_term(Atom('nil'), 'successful_result')
            self.emit("ok = 1;")
            self.emit("while (ok) {")
            self.indent()
            self.emit_save_state()
            self.compile_r(ast.rule)
            self.emit("if (ok) {")
            self.indent()
            self.emit("successful_result = result;")
            self.outdent()
            self.emit("}")
            self.outdent()
            self.emit("}") # endwhile
            self.emit_restore_state()
            self.emit("result = successful_result;")
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
            self.emit(r'result = term_new_from_cstring("expected anything except");')
            self.outdent()
            self.emit("} else {")
            self.indent()
            self.emit("ok = 1;")
            self.emit(r'result = term_new_from_cstring("nil");')
            self.outdent()
            self.emit("}")
            self.outdent()
            self.emit("}")
        elif isinstance(ast, Using):
            prodref = ast.prodref
            scanner_mod = prodref.module or 'main'
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
        elif isinstance(ast, Concat):
            name_lhs = self.compile_r(ast.lhs);
            name_rhs = self.compile_r(ast.rhs);
            name = self.new_name()
            self.emit('struct term *%s = term_concat(term_flatten(%s), term_flatten(%s));' %
                (name, name_lhs, name_rhs)
            )
            return name;
        elif isinstance(ast, TermNode):
            name = self.new_name()
            self.emit_term(ast.to_term(), name);
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
            self.emit("struct term *save_%s;" % local)
        self.emit("int position;")
        self.emit("int reset_position;")

    def emit_save_state(self):
        for local in self.current_branch.locals_:
            self.emit("save_%s = %s;" % (local, local))
        self.emit("position = scanner->position;")
        self.emit("reset_position = scanner->reset_position;")

    def emit_restore_state(self):
        self.emit("scanner->position = position;")
        self.emit("scanner->reset_position = reset_position;")
        for local in self.current_branch.locals_:
            self.emit("%s = save_%s;" % (local, local))

    def emit_term(self, term, name, pattern=False):
        if isinstance(term, Variable):
            if pattern:
                self.emit('struct term *%s = term_new_variable("%s", %s);' %
                    (name, term.name, 'term_new_from_cstring("nil_%s")' % term.name))
            else:
                self.emit('struct term *%s = %s;' % (name, term.name))
        elif isinstance(term, Atom):
            self.emit('struct term *%s = term_new("%s", %s);' %
                (name, escaped(term.text), len(term.text))
            )
        elif isinstance(term, Constructor):
            self.emit('struct term *%s = term_new("%s", %s);' %
                (name, escaped(term.tag), len(term.tag))
            )
            i = 0
            # TODO: reversed() is provisional
            for subterm in reversed(term.contents):
                subname = name + str(i)
                i += 1
                self.emit_term(subterm, subname, pattern=pattern);
                self.emit("term_add_subterm(%s, %s);" % (name, subname))
        else:
            raise NotImplementedError(repr(term))


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
