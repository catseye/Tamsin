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
        buffer[num_read] = '\0';
        if (bufterm == NULL) {
            bufterm = term_new(buffer);
        } else {
            bufterm = term_concat(bufterm, term_new(buffer));
        }
    }

    scanner = scanner_new(bufterm->atom);
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
    def __init__(self, program, outfile):
        self.program = program
        self.prodmap = program[1]
        self.outfile = outfile
        self.indent_ = 0
        self.current_prod = None

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
                formals = prod[2]
                formals = ', '.join(["struct term *" % f for f in formals])
                self.emit("void program_%s(%s);" % (name, formals))
            self.emit("")
            for prod in ast[2]:
                self.compile_r(prod)
        elif ast[0] == 'PROD':
            name = ast[1]
            formals = ast[2]
            locals_ = ast[3]
            body = ast[4]

            self.emit("/*")
            self.emit(repr(ast))
            self.emit("*/")
            formals = ', '.join(["struct term *%s" % f for f in formals])
            self.emit("void program_%s(%s) {" % (name, formals))
            self.indent()
            
            for local in locals_:
                self.emit("struct term *%s;" % local)
            self.emit("")

            self.current_prod = ast
            self.compile_r(body)
            self.current_prod = None

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
                    self.emit_term(args[0], "temp")
                    self.emit('tamsin_expect(scanner, term_flatten(temp)->atom);')
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
                elif name == 'alnum':
                    self.emit('tamsin_alnum(scanner);')
                elif name == 'fail':
                    self.emit_term(args[0], "temp")
                    self.emit("result = temp;")
                    self.emit('ok = 0;')
                else:
                    raise NotImplementedError(name)
            else:
                prodmod = 'program'
                
                i = 0
                for a in args:
                    self.emit_term(a, "temp_arg%s" % i)
                    i += 1
                
                args = ', '.join(["temp_arg%s" % p for p in xrange(0, i)])
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
        elif ast[0] == 'NOT':
            self.emit("{")
            self.indent()
            self.emit_decl_state()
            self.emit_save_state()
            self.compile_r(ast[1])
            self.emit_restore_state()
            self.emit("if (ok) {")
            self.indent()
            self.emit("ok = 0;")
            self.emit(r'result = term_new("expected anything except");')
            self.outdent()
            self.emit("} else {")
            self.indent()
            self.emit("ok = 1;")
            self.emit(r'result = term_new("nil");')
            self.outdent()
            self.emit("}")
            self.outdent()
            self.emit("}")
        else:
            raise NotImplementedError(repr(ast))

    def emit_decl_state(self):
        for local in self.current_prod[3]:
            self.emit("struct term *save_%s;" % local)
        self.emit("int position;")
        self.emit("int reset_position;")

    def emit_save_state(self):
        for local in self.current_prod[3]:
            self.emit("save_%s = %s;" % (local, local))
        self.emit("position = scanner->position;")
        self.emit("reset_position = scanner->reset_position;")

    def emit_restore_state(self):
        self.emit("scanner->position = position;")
        self.emit("scanner->reset_position = reset_position;")
        for local in self.current_prod[3]:
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
            self.emit('struct term *%s = term_new("%s");' % (name, term.name))
            i = 0
            # TODO: reversed() is provisional
            for subterm in reversed(term.contents):
                subname = name + str(i)
                i += 1
                self.emit_term(subterm, subname);
                self.emit("term_add_subterm(%s, %s);" % (name, subname))
