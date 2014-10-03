# encoding: UTF-8

# Copyright (c)2014 Chris Pressey, Cat's Eye Technologies.
# Distributed under a BSD-style license; see LICENSE for more information.

"""
C-generating backend for tamsin.py.  Generated program must be linked
with -ltamsin.

"""

from tamsin.codegen import (
    CodeNode, Program, Prototype, Subroutine, Block, GetVar, Unifier, If
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
        s = "    " * self.indent_ + ''.join(args) + "\n"
        self.outfile.write(s)

    def go(self):
        self.outfile.write(PRELUDE)
        self.traverse(self.codenode)
        self.outfile.write(POSTLUDE)

    def traverse(self, codenode):
        self.outfile.write(repr(self.codenode))


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
