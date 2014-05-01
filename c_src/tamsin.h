/*
 * Copyright (c)2014 Chris Pressey, Cat's Eye Technologies.
 * Distributed under a BSD-style license; see LICENSE for more information.
 */

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* -------------------------------------------------------- terms */

/*
 * If variable field is non-NULL, it is assumed to point to a local
 * variable in a C function.  This will be used during expansion and
 * pattern matching.
 */
struct term {
    char *atom;
    struct term *variable;
    struct term_list *subterms;
};

struct term_list {
    struct term *term;
    struct term_list *next;
};

/*
 * Creates a new "atom" term from the given character string.
 * The new term contains a dynamically allocated copy of the given string,
 *   so the given string may be freed after calling this.
 * Subterms may be added afterwards to turn it into a "constructor" term.
 * Segfaults if there is insufficient memory to allocate the term.
 */
struct term *term_new(const char *);

struct term *term_new_from_char(char c);

struct term *term_new_variable(struct term *);

/*
 * Modifies the given term.
 */
void add_subterm(struct term *, struct term *);

/*
 * Given two "atom" terms, return a new "atom" term consisting of the
 * text of the input terms concatenated together.
 */
struct term *term_concat(const struct term *, const struct term *);

/*
 * Given a possibly non-"atom" term, return a "atom" term consisting of
 * contents of the given term flattened into an atom.
 *
 * Note: for now, the returned term MAY OR MAY NOT be newly allocated.
 */
struct term *term_flatten(struct term *);

/* -------------------------------------------------------- scanner */

struct scanner {
    const char *buffer;
    int position;
    int reset_position;
};

struct scanner *scanner_new(const char *);
char scan(struct scanner *);
void unscan(struct scanner *);
void commit(struct scanner *);

/* -------------------------------------------------------- tamsin */

void tamsin_eof(struct scanner *);
void tamsin_any(struct scanner *);
void tamsin_expect(struct scanner *, char *);
void tamsin_alnum(struct scanner *);

/* --------------------------------------------------------------- */
/* global state: result of last action */

extern int ok;
extern struct term *result;
