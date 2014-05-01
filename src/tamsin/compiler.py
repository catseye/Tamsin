# COMPLETELY EXPERIMENTAL.
# encoding: UTF-8

# spits out some kind of code based on a Tamsin AST.
# certainly does not support `using` or `@` at the moment.

from tamsin.term import Term, Variable, Concat

PRELUDE = r'''
/*
 * Generated code!  Edit at your own risk!
 * Must be linked with -ltamsin to build.
 */
#include <tamsin.h>

/* global state: result of last action */

int ok;
struct term *result;

struct scanner * scanner;
'''

POSTLUDE = r'''
int main(int argc, char **argv) {
    
    scanner = malloc(sizeof(struct scanner));
    scanner->buffer = argv[1];
    scanner->position = 0;
    scanner->reset_position = 0;

    ok = 0;
    result = NULL;

    program_main();

    if (ok) {
        fprintf(stdout, "%s\n", term_flatten(result)->atom);
        exit(0);
    } else {
        fprintf(stderr, "%s\n", term_flatten(result)->atom);
        exit(1);
    }
}
'''

class Compiler(object):
    def __init__(self, outfile, prodmap, localsmap):
        self.outfile = outfile
        self.indent_ = 0
        self.prodmap = prodmap
        self.localsmap = localsmap
        self.current_prod_name = None

    def indent(self):
        self.indent_ += 1

    def outdent(self):
        self.indent_ -= 1

    def emit(self, *args):
        self.outfile.write("    " * self.indent_ + ''.join(args) + "\n")

    def compile(self, ast):
        self.emit(PRELUDE)
        self.compile_r(ast)
        self.emit(POSTLUDE)

    def compile_r(self, ast):
        if ast[0] == 'PROGRAM':
            for prod in ast[2]:
                name = prod[1]
                self.emit("void program_%s(void);" % name)
            self.emit("")
            for prod in ast[2]:
                self.compile_r(prod)
        elif ast[0] == 'PROD':
            name = ast[1]
            formals = ast[2]
            body = ast[3]

            self.emit("/*")
            self.emit(repr(ast))
            self.emit("*/")
            formals = ', '.join(["struct term *%s" % f for f in formals])
            self.emit("void program_%s(%s) {" % (name, formals))
            self.indent()
            
            for local in self.localsmap[name]:
                self.emit("struct term *%s;" % local)
            self.emit("")

            self.current_prod_name = name
            self.compile_r(body)
            self.current_prod_name = None

            self.outdent()
            self.emit("}")
            self.emit("")
        elif ast[0] == 'CALL':
            prodref = ast[1]
            prodmod = prodref[1]
            name = prodref[2]
            args = ast[2]
    
            if prodmod == '$':
                if name == 'expect':
                    term = str(args[0])
                    self.emit('tamsin_expect(scanner, "%s");' % term)
                elif name == 'return':
                    self.emit_term(args[0], "temp")
                    self.emit("result = temp;")
                    self.emit("ok = 1;")
                elif name == 'print':
                    self.emit_term(args[0], "temp")
                    self.emit("result = temp;")
                    self.emit(r'fprintf(stdout, "%s\n", term_flatten(result)->atom);')
                    self.emit("ok = 1;")
                elif name == 'eof':
                    self.emit('tamsin_eof(scanner);')
                elif name == 'any':
                    self.emit('tamsin_any(scanner);')
                elif name == 'fail':
                    self.emit_term(args[0], "temp")
                    self.emit("result = temp;")
                    self.emit('ok = 0;')
                else:
                    raise NotImplementedError(name)
            else:
                prodmod = 'program'
                args = ', '.join(["%s" % a for a in args])
                self.emit("%s_%s(%s);" % (prodmod, name, args))
        elif ast[0] == 'SEND':
            self.compile_r(ast[1])
            # TODO: if ok?
            self.emit("%s = result;" % ast[2].name)
        elif ast[0] == 'SET':
            self.emit_term(ast[2], "temp")
            self.emit("result = temp;")
            self.emit("%s = result;" % ast[1].name)
            self.emit("ok = 1;")
        elif ast[0] == 'AND':
            self.compile_r(ast[1])
            self.emit("if (ok) {")
            self.indent()
            self.compile_r(ast[2])
            self.outdent()
            self.emit("}")
        elif ast[0] == 'OR':
            self.emit("{")
            self.indent()
            self.emit_decl_state()
            self.emit_save_state()
            self.compile_r(ast[1])
            self.emit("if (!ok) {")
            self.indent()
            self.emit_restore_state()
            self.compile_r(ast[2])
            self.outdent()
            self.emit("}")
            self.outdent()
            self.emit("}")
        elif ast[0] == 'WHILE':
            self.emit("{")
            self.indent()
            self.emit_decl_state()
            self.emit_term(Term('nil'), 'successful_result')
            self.emit("ok = 1;")
            self.emit("while (ok) {")
            self.indent()
            self.emit_save_state()
            self.compile_r(ast[1])
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
        else:
            raise NotImplementedError(repr(ast))

    def emit_decl_state(self):
        for local in self.localsmap[self.current_prod_name]:
            self.emit("struct term *save_%s;" % local)
        self.emit("int position;")
        self.emit("int reset_position;")

    def emit_save_state(self):
        for local in self.localsmap[self.current_prod_name]:
            self.emit("save_%s = %s;" % (local, local))
        self.emit("position = scanner->position;")
        self.emit("reset_position = scanner->reset_position;")

    def emit_restore_state(self):
        self.emit("scanner->position = position;")
        self.emit("scanner->reset_position = reset_position;")
        for local in self.localsmap[self.current_prod_name]:
            self.emit("%s = save_%s;" % (local, local))

    def emit_term(self, term, name):
        if isinstance(term, Concat):
            self.emit_term(term.lhs, name + '_lhs')
            self.emit_term(term.rhs, name + '_rhs')
            self.emit('struct term *%s = term_concat(%s_lhs, %s_rhs);' %
                (name, name, name)
            )
        elif isinstance(term, Variable):
            self.emit('struct term *%s = %s;' % (name, term.name))
        else:
            self.emit('struct term *%s = new_term("%s");' % (name, term.name))
            i = 0
            # TODO: reversed() is provisional
            for subterm in reversed(term.contents):
                subname = name + str(i)
                i += 1
                self.emit_term(subterm, subname);
                self.emit("add_subterm(%s, %s);" % (name, subname))
