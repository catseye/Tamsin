/*
 * Copyright (c)2014 Chris Pressey, Cat's Eye Technologies.
 * Distributed under a BSD-style license; see LICENSE for more information.
 */

#include <stdlib.h>
#include <stdio.h>

#ifndef TAMSIN_TERM_H
#define TAMSIN_TERM_H

/*
 * If `subterms` is NULL and `index` == -1, this is an atom.
 * 
 * If `subterms` is non-NULL, this is a constructor.
 *
 * If `index` >= 0, this is a variable.
 *
 * It is not a legal term if both `subterms` is non-NULL and `index` >= 0.
 *
 * In all cases, atom should not be NULL.
 */
struct term {
    const char *atom;
    size_t size;
    int index;
    struct termlist *subterms;
};

struct termlist {
    const struct term *term;
    struct termlist *next;
};

/*
 * Creates a new "atom" term from the given character string.
 * The new term contains a dynamically allocated copy of the given string,
 *   so the given string may be freed after calling this.
 * Subterms may be added afterwards to turn it into a "constructor" term.
 * Segfaults if there is insufficient memory to allocate the term.
 */
const struct term *term_new_atom(const char *, size_t);
const struct term *term_new_atom_from_cstring(const char *);
const struct term *term_new_atom_from_char(char c);

const struct term *term_new_constructor(const char *, size_t,
                                        struct termlist *);
void termlist_add_term(struct termlist **, const struct term *);

const struct term *term_new_variable(const char *, size_t, int);

/*
 * Returns 1 if the atom portion of both terms is identical, otherwise 0.
 */
int term_atoms_equal(const struct term *, const struct term *);

/*
 * Returns 1 if the atom portion of term is identical to given C string, else 0.
 */
int term_atom_cstring_equal(const struct term *, const char *);

/*
 * Given the name of a variable, return the variable term of the
 * same name that is leftmost, uppermost in the given term.
 */
/*
struct term *term_find_variable(const struct term *, const char *);
*/

/*
 * Given two "atom" terms, return a new "atom" term consisting of the
 * text of the input terms concatenated together.
 */
const struct term *term_concat(const struct term *, const struct term *);

/*
 * Given a possibly non-atom term, return an atom consisting of
 * contents of the given term flattened into an atom.
 *
 * The returned term is NOT always newly allocated.
 */
const struct term *term_flatten(const struct term *);

void term_fput(const struct term *, FILE *);

/*
 * Both terms must be ground.
 */
int term_equal(const struct term *, const struct term *);

/*
 * The third argument is an array of struct term *'s.  It will
 * be updated with bindings.
 */
int term_match_unifier(const struct term *, const struct term *,
                       const struct term **);

#endif
