# encoding: UTF-8

# Copyright (c)2014 Chris Pressey, Cat's Eye Technologies.
# Distributed under a BSD-style license; see LICENSE for more information.

"""
C-generating backend for tamsin.py.  Generated program must be linked
with -ltamsin.

"""

from tamsin.codegen import (
    CodeNode, Program, Prototype, Subroutine,
    Block, If, While, And, Not, Return, Builtin, Call, Truth,
    DeclareLocal, GetVar, SetVar,
    Unifier, PatternMatch, NoMatch,
    DeclState, SaveState, RestoreState,
)
from tamsin.ast import AtomNode   # bah
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

class Emitter(object):
    def __init__(self, codenode, outfile):
        self.codenode = codenode
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
        s = "    " * self.indent_ + ''.join(args)
        self.outfile.write(s)

    def emitln(self, *args):
        s = "    " * self.indent_ + ''.join(args) + "\n"
        self.outfile.write(s)

    # kontinue the line
    def emitk(self, *args):
        self.outfile.write(''.join(args))

    def emitkln(self, *args):
        self.outfile.write(''.join(args) + "\n")

    def go(self):
        self.outfile.write(PRELUDE)
        self.traverse(self.codenode)
        self.outfile.write(POSTLUDE)

    def traverse(self, codenode):
        if isinstance(codenode, Program):
            for arg in codenode.args:
                self.traverse(arg)
        elif isinstance(codenode, Prototype):
            self.emitln("void prod_%s_%s(%s);" % (
                codenode['module'].name, codenode['prod'].name,
                ', '.join(["const struct term *"
                           for f in codenode['formals']])
            ))
        elif isinstance(codenode, Subroutine):
            fmls = []
            for (i, f) in enumerate(codenode['formals']):
                fmls.append("const struct term *i%s" % i)
            fmls = ', '.join(fmls)

            self.emitln("void prod_%s_%s(%s) {" %
                (codenode['module'].name, codenode['prod'].name, fmls)
            )
            self.indent()
            for arg in codenode.args:
                self.traverse(arg)  
            self.outdent()
            self.emitln("}")
        elif isinstance(codenode, Unifier):
            self.emitln("/* %r */" % codenode)
        elif isinstance(codenode, If):
            self.emit("if (")
            self.traverse(codenode[0])
            self.emitkln(") {")
            self.indent()
            self.traverse(codenode[1])
            self.outdent()
            if len(codenode.args) == 3:
                self.emitln("} else {")
                self.indent()
                self.traverse(codenode[2])
                self.outdent()
            self.emitln("}")
        elif isinstance(codenode, While):
            self.emit("while (")
            self.traverse(codenode[0])
            self.emitkln(") {")
            self.indent()
            self.traverse(codenode[1])
            self.outdent()
            self.emitln("}")
        elif isinstance(codenode, Not):
            self.emitk("(!(")
            self.traverse(codenode[0])
            self.emitk("))")
        elif isinstance(codenode, Truth):
            self.emitk("1")
        elif isinstance(codenode, Block):
            for arg in codenode.args:
                self.traverse(arg)
        elif isinstance(codenode, DeclareLocal):
            self.emit("const struct term *%s = " % codenode[0])
            self.traverse(codenode[1])
            self.emitkln(';')
        elif isinstance(codenode, Call):
            self.emitln("prod_%s_%s(%s);" %
                (codenode['module'], codenode['name'], '')
            )
        elif isinstance(codenode, GetVar):
            self.emitk(codenode[0])
        elif isinstance(codenode, SetVar):
            self.emit(codenode[0])
            self.emitk(' = ')
            self.emitk(codenode[1])
            self.emitkln(';')
        elif isinstance(codenode, Builtin):
            if codenode['name'] == 'print':
                self.emit("result = ")
                self.traverse(codenode[0])
                self.emitkln(';')
                self.emitln("term_fput(result, stdout);")
                self.emitln(r'fwrite("\n", 1, 1, stdout);')
                self.emitln("ok = 1;")
            elif codenode['name'] == 'return':
                self.emit("result = ")
                self.traverse(codenode[0])
                self.emitkln(';')
            elif codenode['name'] == 'expect':
                self.emit('tamsin_expect(scanner, ')
                self.traverse(codenode[0])
                self.emitkln(');')
            else:
                raise NotImplementedError(repr(codenode))
        elif isinstance(codenode, AtomNode):
            self.emitk('term_new_atom_from_cstring("%s")' % codenode.text)
        elif isinstance(codenode, Return):
            self.emitln("return;")
        elif isinstance(codenode, NoMatch):
            self.emitln('result = term_new_atom_from_cstring'
                      '("No \'%s\' production matched arguments ");' %
                      codenode['prod'].name)
            for i in xrange(0, len(codenode['formals'])):
                self.emitln('result = term_concat(result, term_flatten(i%d));' % i)
                self.emitln('result = term_concat(result, term_new_atom_from_cstring(", "));')
            self.emitln("ok = 0;")
        elif isinstance(codenode, DeclState):
            for local in []:  # self.current_branch.locals_:
                self.emitln("const struct term *save_%s;" % local)
            self.emitln("int position;")
            self.emitln("int reset_position;")
            self.emitln("const char *buffer;")
            self.emitln("int buffer_size;")
            self.emitln("")
        elif isinstance(codenode, SaveState):
            for local in []:  # self.current_branch.locals_:
                self.emitln("save_%s = %s;" % (local, local))
            self.emitln("position = scanner->position;")
            self.emitln("reset_position = scanner->reset_position;")
            self.emitln("buffer = scanner->buffer;")
            self.emitln("buffer_size = scanner->size;")
        elif isinstance(codenode, RestoreState):
            self.emitln("scanner->position = position;")
            self.emitln("scanner->reset_position = reset_position;")
            self.emitln("scanner->buffer = buffer;")
            self.emitln("scanner->size = buffer_size;")
            for local in []:  # self.current_branch.locals_:
                self.emitln("%s = save_%s;" % (local, local))
        else:
            raise NotImplementedError(repr(codenode))


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
