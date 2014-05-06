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

struct term *term_new(const char *atom, size_t size) {
    struct term *t;

    t = malloc(sizeof(struct term));
    t->atom = malloc(size);
    memcpy(t->atom, atom, size);
    t->size = size;
    t->storing = NULL;
    t->subterms = NULL;
}

struct term tamsin_EOF = {"EOF", 3, NULL, NULL};

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
}

void term_add_subterm(struct term *term, struct term *subterm) {
    struct term_list *tl;

    assert(term->storing == NULL);
    tl = malloc(sizeof(struct term_list));
    tl->term = subterm;
    tl->next = term->subterms;
    term->subterms = tl;        
}

struct term *term_find_variable(const struct term *t, const char *name) {
    struct term_list * tl;

    if (t->storing != NULL && !strcmp(name, t->atom)) {
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

struct term *term_flatten(struct term *t) {
    struct term_list *tl;

    if (t->storing != NULL) {          /* it's an variable; get its value */
        return term_flatten(t->storing);
    } else if (t->subterms == NULL) {  /* it's an atom */
        return t;
    } else {                           /* it's a constructor */
        struct term *n;
        /* XXX why do we clone t here? */
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
    term_format_r(t);
}

void term_fput(struct term *t, FILE *f) {
    struct term *flat = term_flatten(t);
    fprintf(f, "%s", flat->atom);
}

int term_match(struct term *pattern, struct term *ground)
{
    struct term_list *tl1, *tl2;

    //term_fput(pattern, stdout);
    //printf(" ?= ");
    //term_fput(ground, stdout);
    //printf("...\n");

    assert(ground->storing == NULL);

    if (pattern->storing != NULL) {
        pattern->storing = ground;
        //printf("unified, YES\n");
        return 1;
    }
    if (strcmp(pattern->atom, ground->atom)) {
        //printf("not same atom ('%s' vs '%s'), NO\n", pattern->atom, ground->atom);
        return 0;
    }
    if (pattern->subterms == NULL && ground->subterms == NULL) {
        //printf("same atom, YES\n");
        return 1;
    }

    tl1 = pattern->subterms;
    tl2 = ground->subterms;
    while (tl1 != NULL && tl2 != NULL) {
        if (!term_match(tl1->term, tl2->term)) {
            //printf("no submatch, NO\n");
            return 0;
        }
        tl1 = tl1->next;
        tl2 = tl2->next;
    }
    if (tl1 != NULL || tl2 != NULL) {
        /* not the same # of subterms */
        //printf("not same # of subterms, NO\n");
        return 0;
    }
    //printf("subterms match, YES\n");
    return 1;
}
