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

struct term *term_new(const char *atom) {
    struct term *t;
    t = malloc(sizeof(struct term));
    t->atom = strdup(atom);
    t->variable = NULL;
    t->subterms = NULL;
}

struct term *term_new_from_char(char c) {
    char s[2];
    s[0] = c;
    s[1] = '\0';
    return term_new(s);
}

struct term *term_new_variable(struct term *v) {
    struct term *t;
    t = malloc(sizeof(struct term));
    t->atom = NULL;
    t->variable = v;
    t->subterms = NULL;
}

void term_add_subterm(struct term *term, struct term *subterm) {
    struct term_list *tl;
    tl = malloc(sizeof(struct term_list));
    tl->term = subterm;
    tl->next = term->subterms;
    term->subterms = tl;        
}

struct term *term_concat(const struct term *lhs, const struct term *rhs) {
    struct term *t;
    int new_size;
    char *new_atom;

    assert(lhs->subterms == NULL);
    assert(rhs->subterms == NULL);

    if (lhs->variable != NULL) {
        lhs = lhs->variable;
    }
    if (rhs->variable != NULL) {
        rhs = rhs->variable;
    }

    new_size = strlen(lhs->atom) + strlen(rhs->atom);
    new_atom = malloc(new_size + 1);
    strcpy(new_atom, lhs->atom);
    strcat(new_atom, rhs->atom);
    t = term_new(new_atom);
    free(new_atom);

    return t;
}

const struct term BRA = { "(", NULL };
const struct term KET = { ")", NULL };
const struct term COMMA = { ", ", NULL };

struct term *term_flatten(struct term *t) {
    struct term_list *tl;

    if (t->variable != NULL) {  /* it's an variable; get its value */
        return term_flatten(t->variable);
    } else if (t->subterms == NULL) {  /* it's an atom */
        return t;
    } else {                    /* it's a constructor */
        struct term *n;
        n = term_concat(term_new(t->atom), &BRA);

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
