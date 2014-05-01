# COMPLETELY EXPERIMENTAL.
# encoding: UTF-8

# spits out some kind of code based on a Tamsin AST.
# certainly does not support `using` or `@` at the moment.

from tamsin.term import Term, Variable

PRELUDE = r'''
/*
 * Generated code!  Edit at your own risk!
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* global state: result of last action */

int ok;
struct term *result;

/* terms */

struct term {
    const char *atom;
    struct term_list *subterms;
};

struct term_list {
    struct term *term;
    struct term_list *next;
};

struct term *new_term(const char *atom) {
    struct term *t;
    t = malloc(sizeof(struct term));
    t->atom = strdup(atom);
    t->subterms = NULL;
}

void add_subterm(struct term *term, struct term *subterm) {
    struct term_list *tl;
    tl = malloc(sizeof(struct term_list));
    tl->term = subterm;
    tl->next = term->subterms;
    term->subterms = tl;        
}

char fmtbuf[1000];  /* yeesh */

void term_format_r(struct term *t) {
    struct term_list *tl;

    strcat(fmtbuf, t->atom);
    if (t->subterms != NULL) {
        strcat(fmtbuf, "(");
        
        for (tl = t->subterms; tl != NULL; tl = tl->next) {
            term_format_r(tl->term);
            if (tl->next != NULL) {
                strcat(fmtbuf, ", ");
            }
        }
        
        strcat(fmtbuf, ")");
    }
}

char *term_format(struct term *t) {
    strcpy(fmtbuf, "");
    term_format_r(t);
    return fmtbuf;
}

/* scanner */

struct scanner {
    char *buffer;
    int position;
    int reset_position;
};

char scan(struct scanner *s) {
    char c = s->buffer[s->position];
    if (c == '\0') {
        return '\0';
    } else {
        s->position++;
        return c;
    }
};

void unscan(struct scanner *s) {
    s->position = s->reset_position;
}

void commit(struct scanner *s) {
    s->reset_position = s->position;
}

void tamsin_eof(struct scanner *s) {
    char c = scan(s);
    unscan(s);
    if (c == '\0') {
        result = new_term("EOF");
        ok = 1;
    } else {
        char t[100];
        sprintf(t, "expected EOF found '%c'", c);
        result = new_term(t);
        ok = 0;
    }
}

void tamsin_any(struct scanner *s) {
    char c = scan(s);
    if (c == '\0') {
        unscan(s);
        result = new_term("expected any token, found EOF");
        ok = 0;
    } else {
        char t[2];
        commit(s);
        sprintf(t, "%c", c);
        result = new_term(t);
        ok = 1;
    }
}

void tamsin_expect(struct scanner *s, char *token) {
    char c = scan(s);
    if (c == token[0]) {
        commit(s);
        char s[10];
        strcpy(s, "a");
        s[0] = c;
        result = new_term(s);
        ok = 1;
    } else {
        unscan(s);
        char s[100];
        sprintf(s, "expected '%c' found '%c'", token[0], c);
        result = new_term(s);
        ok = 0;
    }
};

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
        fprintf(stdout, "%s\n", term_format(result));
        exit(0);
    } else {
        fprintf(stderr, "%s\n", term_format(result));
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
                    self.emit(r'fprintf(stdout, "%s\n", term_format(result));')
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
        if isinstance(term, Variable):
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
