# COMPLETELY EXPERIMENTAL.

# spits out some kind of code based on a Tamsin AST.
# certainly does not support `using` or `@` at the moment.

PRELUDE = """
/* an example of what I would hope a Tamsin->C compiler to produce.
   but this was written by hand. */

/* scanner */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

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

int consume(struct scanner *s, char *token) {
    char c = scan(s);
    //fprintf(stderr, "scanned '%c'\n", c);
    if (c == token[0]) {
        commit(s);
        //fprintf(stderr, "committed '%c'\n", c);
        return 1;
    } else {
        unscan(s);
        //fprintf(stderr, "rollbacked '%c'\n", c);
        return 0;
    }
};


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
    t->atom = atom;
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
                strcat(fmtbuf, ",");
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

/* globals */

struct scanner * scanner;

/* result of last production */

int ok;
struct term *result;

"""

POSTLUDE = """

/* driver */

int main(int argc, char **argv) {
    
    scanner = malloc(sizeof(struct scanner));
    scanner->buffer = "0000";
    scanner->position = 0;
    scanner->reset_position = 0;

    ok = 0;
    result = NULL;

    tamsin_main();

    if (ok) {
        //fprintf(stderr, "done\n");
        fprintf(stdout, "%s\n", term_format(result));
        exit(0);
    } else {
        fprintf(stderr, "Error message\n");
        exit(1);
    }
}
"""

def compile(ast, out):
    out.write(PRELUDE)
    compile_r(ast, out)
    out.write(POSTLUDE)

def compile_r(ast, out):
    if ast[0] == 'PROGRAM':
        for prod in ast[2]:
            name = prod[1]
            out.write("void tamsin_%s(void);\n" % name)
        out.write("\n")
        for prod in ast[2]:
            compile_r(prod, out)
    elif ast[0] == 'PROD':
        name = ast[1]
        formals = ast[2]
        body = ast[3]
        
        #formals = ', '.join(["struct term *%s" % f for f in formals])
        out.write("void tamsin_%s(void) {\n" % name)
        
        locals_ = []
        collect_locals(body, locals_)
        for local in locals_:
            out.write("    struct term *%s;\n" % local)
        out.write("\n")
        
        #out.write("int %s(%s) {\n" % (name, formals))
        compile_r(body, out)
        out.write("}\n\n")
    elif ast[0] == 'CALL':
        prodref = ast[1]
        #prodmod = prodref[1]
        name = prodref[2]
        args = ast[2]

        #args = ', '.join(["%s" % a for a in args])
        args = ''
        out.write("    tamsin_%s(%s);\n" % (name, args))
    elif ast[0] == 'SEND':
        out.write("  %s = (\n" % ast[2].name)
        compile_r(ast[1], out)
        out.write("  );\n")
    elif ast[0] == 'SET':
        out.write("  %s = (\n" % ast[1].name)
        compile_r(ast[2], out)
        out.write("  );\n")
    elif ast[0] == 'AND':
        compile_r(ast[1], out)
        out.write("    if (ok) {\n")
        compile_r(ast[2], out)
        out.write("    }\n")
    elif ast[0] == 'OR':
        compile_r(ast[1], out)
        out.write("    if (!ok) {\n")
        compile_r(ast[2], out)
        out.write("    }\n")
    else:
        raise NotImplementedError(repr(ast))


def collect_locals(ast, locals_):
    if ast[0] == 'SEND':
        locals_.append(ast[2].name)
    elif ast[0] == 'SET':
        locals_.append(ast[1].name)
    elif ast[0] == 'AND':
        collect_locals(ast[1], locals_)
        collect_locals(ast[2], locals_)
    elif ast[0] == 'OR':
        collect_locals(ast[1], locals_)
        collect_locals(ast[2], locals_)


# void tamsin_zeroes(void) {
#     struct term *E;
# 

#     if (consume(scanner, "0")) {
#         tamsin_zeroes();
#         E = result;
#         if (ok) {
#             struct term *temp = new_term("zero");
#             add_subterm(temp, E);
#             result = temp;
#         }
#     } else {
#         ok = 1;
#         struct term *temp = new_term("nil");
#         result = temp;
#     }
# }
