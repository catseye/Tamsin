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

struct term tamsin_EOF = {"EOF", 3, -1, NULL};
 
struct term *term_new(const char *atom, size_t size) {
    struct term *t;
    char *text;

    t = malloc(sizeof(struct term));
    text = malloc(size);
    memcpy(text, atom, size);
    t->atom = text;
    t->size = size;
    t->index = -1;
    t->subterms = NULL;

    return t;
}

void termlist_add_term(struct term_list **tl, const struct term *term) {
    struct term_list *new_tl;

    new_tl = malloc(sizeof(struct term_list));
    new_tl->term = term;
    new_tl->next = *tl;
    *tl = new_tl;
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

struct term *term_new_variable(const char *name, int index) {
    struct term *t = term_new(name, strlen(name));

    t->index = index;

    return t;
}

void term_add_subterm(struct term *term, const struct term *subterm) {
    struct term_list *tl;

    assert(term->index == -1);
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

struct term *term_concat(const struct term *lhs, const struct term *rhs) {
    struct term *t;
    int new_size;
    char *new_atom;

    assert(lhs->subterms == NULL);
    assert(rhs->subterms == NULL);

    new_size = lhs->size + rhs->size;
    new_atom = malloc(new_size);
    memcpy(new_atom, lhs->atom, lhs->size);
    memcpy(new_atom + lhs->size, rhs->atom, rhs->size);
    t = term_new(new_atom, new_size);
    free(new_atom);

    return t;
}

const struct term BRA = { "(", 1, -1, NULL };
const struct term KET = { ")", 1, -1, NULL };
const struct term COMMA = { ", ", 2, -1, NULL };

const struct term *term_flatten(const struct term *t) {
    struct term_list *tl;

    if (t->subterms == NULL) {  /* it's an atom */
        return t;
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
    const struct term *flat = term_flatten(t);

    fwrite(flat->atom, 1, flat->size, f);
}

/*
 * Returns the number of extra bytes we'll need to allocate to escape
 * this string.  0 indicates it does not need to be escaped.
 * control/high character = +3  (\xXX)
 * apos or backslash      = +1  (\\, \')
 */
int escapes_needed(const char *text, size_t size) {
    int i;
    int needed = 0;

    for (i = 0; i < size; i++) {
        if (text[i] < 32 || text[i] > 126) {
            needed += 3;
        } else if (text[i] == '\'' || text[i] == '\\') {
            needed += 1;
        }
    }
    
    return needed;
}

int all_bareword(const char *text, size_t size) {
    int i;

    for (i = 0; i < size; i++) {
        if (tamsin_isalnum(text[i]) || text[i] == '_') {
        } else {
            return 0;
        }
    }
    
    return 1;
}

const char *HEX = "0123456789abcdef";

const struct term *term_escape_atom(const struct term *t) {
    int needed;
    
    if (t->size == 0) {
        return term_new("''", 2);
    }

    needed = escapes_needed(t->atom, t->size);

    if (needed > 0) {
        struct term *r;
        char *buffer = malloc(t->size + needed);
        int i, j = 0;

        for (i = 0; i < t->size; i++) {
            if (t->atom[i] < 32 || t->atom[i] > 126) {
                buffer[j++] = '\\';
                buffer[j++] = 'x';
                buffer[j++] = HEX[(t->atom[i] >> 4) & 0x0f];
                buffer[j++] = HEX[t->atom[i] & 0x0f];
            } else if (t->atom[i] == '\'' || t->atom[i] == '\\') {
                buffer[j++] = '\\';
                buffer[j++] = t->atom[i];
            } else {
                buffer[j++] = t->atom[i];
            }
        }
        assert(j == t->size + needed);

        r  = term_new("'", 1);
        r = term_concat(r, term_new(buffer, t->size + needed));
        r = term_concat(r, term_new("'", 1));
        free(buffer);

        return r;
    } else if (all_bareword(t->atom, t->size)) {
        /* TODO: can we eliminate this copy? */
        return term_new(t->atom, t->size);
    } else {
        const struct term *r;

        r = term_new("'", 1);
        r = term_concat(r, t);
        r = term_concat(r, term_new("'", 1));

        return r;
    }
}

const struct term *term_repr(const struct term *t) {
    struct term_list *tl;

    if (t->subterms == NULL) {  /* it's an atom */
        return term_escape_atom(t);
    } else {                           /* it's a constructor */
        struct term *n;
        n = term_concat(term_escape_atom(t), &BRA);

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

int term_equal(const struct term *pattern, const struct term *ground)
{
    struct term_list *tl1, *tl2;

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
    struct term_list *tl1, *tl2;

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
