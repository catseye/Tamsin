/*
 * Copyright (c)2014 Chris Pressey, Cat's Eye Technologies.
 * Distributed under a BSD-style license; see LICENSE for more information.
 */

#include <assert.h>
#include <string.h>
#include <stdlib.h>
#include <stdio.h>

#include "term.h"

/*
 * this code LEAKS MEMORY all over the place, but that's "ok" because
 * Tamsin programs "aren't long running".  and it's better than having
 * buffer overflows.
 */

struct term tamsin_EOF = {"EOF", 3, -1, NULL};

struct term *term_single_byte_table = NULL;
char term_single_byte_data[256];

const struct term *term_new_atom(const char *atom, size_t size) {
    struct term *t;
    char *text;

    if (size == 1) {
        int i;
        if (term_single_byte_table == NULL) {
            term_single_byte_table = malloc(sizeof(struct term) * 256);
            for (i = 0; i < 256; i++) {
                term_single_byte_data[i] = (char)i;
                term_single_byte_table[i].atom = term_single_byte_data + i;
                term_single_byte_table[i].size = 1;
                term_single_byte_table[i].index = -1;
                term_single_byte_table[i].subterms = NULL;
            }
        }
        i = ((unsigned char *)atom)[0];
        return &term_single_byte_table[i];
    }

    t = malloc(sizeof(struct term));
    text = malloc(size);
    memcpy(text, atom, size);
    t->atom = text;
    t->size = size;
    t->index = -1;
    t->subterms = NULL;

    return t;
}

const struct term *term_new_atom_from_char(char c) {
    char s[2];

    s[0] = c;
    s[1] = '\0';

    return term_new_atom(s, 1);
}

const struct term *term_new_atom_from_cstring(const char *atom) {
    return term_new_atom(atom, strlen(atom));
}

const struct term *term_new_constructor(const char *tag, size_t size,
                                        struct termlist *subterms)
{
    struct term *t = malloc(sizeof(struct term));
    char *text = malloc(size);

    memcpy(text, tag, size);
    t->atom = text;
    t->size = size;
    t->index = -1;
    t->subterms = subterms;

    return t;
}

void termlist_add_term(struct termlist **tl, const struct term *term) {
    struct termlist *new_tl;

    new_tl = malloc(sizeof(struct termlist));
    new_tl->term = term;
    new_tl->next = *tl;
    *tl = new_tl;
}

const struct term *term_new_variable(const char *name, size_t size, int index) {
    struct term *t;
    char *text;

    t = malloc(sizeof(struct term));
    text = malloc(size);
    memcpy(text, name, size);
    t->atom = text;
    t->size = size;
    assert(index != -1);
    t->index = index;
    t->subterms = NULL;

    return t;
}

int term_atoms_equal(const struct term *lhs, const struct term *rhs) {
    if (lhs->size != rhs->size) {
        return 0;
    }
    return memcmp(lhs->atom, rhs->atom, lhs->size) == 0;
}

int term_atom_cstring_equal(const struct term *lhs, const char *string) {
    if (lhs->size != strlen(string)) {
        return 0;
    }
    return memcmp(lhs->atom, string, lhs->size) == 0;
}

const struct term *term_concat(const struct term *lhs, const struct term *rhs) {
    const struct term *t;
    int new_size;
    char *new_atom;

    assert(lhs->subterms == NULL);
    assert(rhs->subterms == NULL);

    new_size = lhs->size + rhs->size;
    new_atom = malloc(new_size);
    memcpy(new_atom, lhs->atom, lhs->size);
    memcpy(new_atom + lhs->size, rhs->atom, rhs->size);
    t = term_new_atom(new_atom, new_size);
    free(new_atom);

    return t;
}

const struct term COMMASPACE = { ", ", 2, -1, NULL };

const struct term *term_flatten(const struct term *t) {
    struct termlist *tl;

    if (t->subterms == NULL) {  /* it's an atom */
        return t;
    } else {                           /* it's a constructor */
        const struct term *n;
        /* we clone t here to get an atom from its tag */
        n = term_concat(term_new_atom(t->atom, t->size),
                        term_new_atom_from_char('('));

        for (tl = t->subterms; tl != NULL; tl = tl->next) {
            n = term_concat(n, term_flatten(tl->term));
            if (tl->next != NULL) {
                n = term_concat(n, &COMMASPACE);
            }
        }
        n = term_concat(n, term_new_atom_from_char(')'));
        return n;
    }
}

void term_fput(const struct term *t, FILE *f) {
    const struct term *flat = term_flatten(t);

    fwrite(flat->atom, 1, flat->size, f);
}

int term_equal(const struct term *pattern, const struct term *ground)
{
    struct termlist *tl1, *tl2;

    assert(pattern->index == -1);
    assert(ground->index == -1);

    if (!term_atoms_equal(pattern, ground)) {
        return 0;
    }
    if (pattern->subterms == NULL && ground->subterms == NULL) {
        return 1;
    }

    tl1 = pattern->subterms;
    tl2 = ground->subterms;
    while (tl1 != NULL && tl2 != NULL) {
        if (!term_equal(tl1->term, tl2->term)) {
            return 0;
        }
        tl1 = tl1->next;
        tl2 = tl2->next;
    }
    if (tl1 != NULL || tl2 != NULL) {
        return 0;
    }
    return 1;
}

int term_match_unifier(const struct term *pattern, const struct term *ground,
                       const struct term **variables)
{
    struct termlist *tl1, *tl2;

    if (pattern->index >= 0) {
        variables[pattern->index] = ground;
        return 1;
    }
    if (!term_atoms_equal(pattern, ground)) {
        return 0;
    }
    if (pattern->subterms == NULL && ground->subterms == NULL) {
        return 1;
    }

    tl1 = pattern->subterms;
    tl2 = ground->subterms;
    while (tl1 != NULL && tl2 != NULL) {
        if (!term_match_unifier(tl1->term, tl2->term, variables)) {
            return 0;
        }
        tl1 = tl1->next;
        tl2 = tl2->next;
    }
    if (tl1 != NULL || tl2 != NULL) {
        return 0;
    }

    return 1;
}
