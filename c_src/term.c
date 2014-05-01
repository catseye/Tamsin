/*
 * Copyright (c)2014 Chris Pressey, Cat's Eye Technologies.
 * Distributed under a BSD-style license; see LICENSE for more information.
 */

#include "tamsin.h"

/*
 * this code LEAKS MEMORY all over the place, but that's "ok" because
 * Tamsin programs "aren't long running".  and it's better than having
 * buffer overflows.
 */

/*
 * Creates a new "atom" term from the given character string.
 * The new term contains a dynamically allocated copy of the given string,
 *   so the given string may be freed after calling this.
 * Subterms may be added afterwards to turn it into a "constructor" term.
 * Segfaults if there is insufficient memory to allocate the term.
 */
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

/*
 * Given two "atom" terms, return a new "atom" term consisting of the
 * text of the input terms concatenated together.
 */
struct term *term_concat(const struct term *lhs, const struct term *rhs) {
    struct term *t;
    int new_size;
    char *new_atom;

    assert(lhs->subterms == NULL);
    assert(rhs->subterms == NULL);

    new_size = strlen(lhs->atom) + strlen(rhs->atom);
    new_atom = malloc(new_size + 1);
    strcpy(new_atom, lhs->atom);
    strcat(new_atom, rhs->atom);
    t = new_term(new_atom);
    free(new_atom);

    return t;
}

const struct term BRA = { "(", NULL };
const struct term KET = { ")", NULL };
const struct term COMMA = { ", ", NULL };

/*
 * Given a possibly non-"atom" term, return a "atom" term consisting of
 * contents of the given term flattened into an atom.
 *
 * Note: for now, the returned term MAY OR MAY NOT be newly allocated.
 */
struct term *term_flatten(struct term *t) {
    struct term_list *tl;

    if (t->subterms == NULL) {  /* it's an atom */
        return t;
    } else {                    /* it's a constructor */
        struct term *n;
        n = term_concat(new_term(t->atom), &BRA);

        for (tl = t->subterms; tl != NULL; tl = tl->next) {
            n = term_concat(n, term_flatten(tl->term));
            if (tl->next != NULL) {
                n = term_concat(n, &COMMA);
            }
        }
        n = term_concat(n, &KET);
        return n;
    }
    term_format_r(t);
}
