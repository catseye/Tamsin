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

struct term tamsin_EOF = {"EOF", 3, NULL, NULL};

struct term *term_new(const char *atom, size_t size) {
    struct term *t;

    t = malloc(sizeof(struct term));
    t->atom = malloc(size);
    memcpy(t->atom, atom, size);
    t->size = size;
    t->storing = NULL;
    t->subterms = NULL;

    return t;
}

void termlist_add_term(struct term_list **tl, struct term *term) {
    struct term_list *new_tl;

    new_tl = malloc(sizeof(struct term_list));
    new_tl->term = term;
    new_tl->next = *tl;
    *tl = new_tl;
}

/*
 * Must be a ground term.
 */
struct term *term_deep_copy(const struct term *term) {
    struct term *new_term = term_new(term->atom, term->size);
    struct term_list *new_tl = NULL, *tl;

    assert(term->storing == NULL);

    for (tl = term->subterms; tl != NULL; tl = tl->next) {
        struct term *copy = term_deep_copy(tl->term);
        termlist_add_term(&new_tl, copy);
    }

    for (tl = new_tl; tl != NULL; tl = tl->next) {
        term_add_subterm(new_term, tl->term);
    }

    /* termlist_free(new_tl); */
    return new_term;
}

struct term *term_new_from_char(char c) {
    char s[2];

    s[0] = c;
    s[1] = '\0';

    return term_new(s, 1);
}

struct term *term_new_from_cstring(const char *atom) {
    return term_new(atom, strlen(atom));
}

struct term *term_new_variable(const char *name, struct term *v) {
    struct term *t = term_new(name, strlen(name));

    t->storing = v;

    return t;
}

void term_add_subterm(struct term *term, struct term *subterm) {
    struct term_list *tl;

    assert(term->storing == NULL);
    tl = malloc(sizeof(struct term_list));
    tl->term = subterm;
    tl->next = term->subterms;
    term->subterms = tl;        
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

struct term *term_find_variable(const struct term *t, const char *name) {
    struct term_list * tl;

    if (t->storing != NULL && term_atom_cstring_equal(t, name)) {
        return t->storing;
    }
    
    for (tl = t->subterms; tl != NULL; tl = tl->next) {
        struct term *f = term_find_variable(tl->term, name);
        if (f != NULL) {
            return f;
        }
    }

    return NULL;
}

struct term *term_concat(const struct term *lhs, const struct term *rhs) {
    struct term *t;
    int new_size;
    char *new_atom;

    assert(lhs->subterms == NULL);
    assert(rhs->subterms == NULL);

    if (lhs->storing != NULL) {
        lhs = lhs->storing;
    }
    if (rhs->storing != NULL) {
        rhs = rhs->storing;
    }

    new_size = lhs->size + rhs->size;
    new_atom = malloc(new_size);
    memcpy(new_atom, lhs->atom, lhs->size);
    memcpy(new_atom + lhs->size, rhs->atom, rhs->size);
    t = term_new(new_atom, new_size);
    free(new_atom);

    return t;
}

const struct term BRA = { "(", 1, NULL, NULL };
const struct term KET = { ")", 1, NULL, NULL };
const struct term COMMA = { ", ", 2, NULL, NULL };

struct term *term_flatten(const struct term *t) {
    struct term_list *tl;

    if (t->storing != NULL) {          /* it's a variable; get its value */
        return term_flatten(t->storing);
    } else if (t->subterms == NULL) {  /* it's an atom */
        return term_new(t->atom, t->size);
    } else {                           /* it's a constructor */
        struct term *n;
        /* we clone t here to get an atom from its tag */
        n = term_concat(term_new(t->atom, t->size), &BRA);

        for (tl = t->subterms; tl != NULL; tl = tl->next) {
            n = term_concat(n, term_flatten(tl->term));
            if (tl->next != NULL) {
                n = term_concat(n, &COMMA);
            }
        }
        n = term_concat(n, &KET);
        return n;
    }
}

void term_fput(const struct term *t, FILE *f) {
    struct term *flat = term_flatten(t);

    fwrite(flat->atom, 1, flat->size, f);
}

int is_printable_bare(const char *text, size_t size) {
    int i;

    for (i = 0; i < size; i++) {
        if (text[i] < 32 || text[i] > 126 ||
            text[i] == '\'' || text[i] == '\\') {
            return 0;
        }
    }
    
    return 1;
}

struct term *term_escape(const struct term *t) {
    return term_new(t->atom, t->size); /* NOT TRUE */
}

struct term *term_repr(const struct term *t) {
    struct term_list *tl;

    if (t->storing != NULL) {          /* it's a variable; get its value */
        return term_repr(t->storing);
    } else if (t->subterms == NULL) {  /* it's an atom */
        if (is_printable_bare(t->atom, t->size)) {
            return term_new(t->atom, t->size);
        } else {
            struct term *r = term_new("'", 1);
            r = term_concat(r, term_escape(t));
            r = term_concat(r, term_new("'", 1));
            return r;
        }
    } else {                           /* it's a constructor */
        struct term *n;
        /* we clone t here to get an atom from its tag */
        n = term_concat(term_new(t->atom, t->size), &BRA);

        for (tl = t->subterms; tl != NULL; tl = tl->next) {
            n = term_concat(n, term_repr(tl->term));
            if (tl->next != NULL) {
                n = term_concat(n, &COMMA);
            }
        }
        n = term_concat(n, &KET);
        return n;
    }
}

int term_match(struct term *pattern, struct term *ground)
{
    struct term_list *tl1, *tl2;

    assert(ground->storing == NULL);

    if (pattern->storing != NULL) {
        pattern->storing = ground;
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
        if (!term_match(tl1->term, tl2->term)) {
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
