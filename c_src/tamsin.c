/*
 * Copyright (c)2014 Chris Pressey, Cat's Eye Technologies.
 * Distributed under a BSD-style license; see LICENSE for more information.
 */

/*
 * TODO: less term_new_from_cstring, please -- not for tokens etc.
 */
#include "tamsin.h"

#include <ctype.h>

struct term APOS = {"'", 1, NULL, NULL};

void tamsin_eof(struct scanner *s) {
    struct term *t = scan(s);
    unscan(s);
    if (t == &tamsin_EOF) {
        result = t;
        ok = 1;
    } else {
        result = term_new_from_cstring("expected EOF found '");
        result = term_concat(result, t);
        result = term_concat(result, &APOS);
        ok = 0;
    }
}

void tamsin_any(struct scanner *s) {
    struct term *t = scan(s);
    if (t == &tamsin_EOF) {
        unscan(s);
        result = term_new_from_cstring("expected any token, found EOF");
        ok = 0;
    } else {
        commit(s);
        result = t;
        ok = 1;
    }
}

void tamsin_expect(struct scanner *s, const struct term *expected) {
    struct term *scanned = scan(s);
    if (scanned != &tamsin_EOF && term_atoms_equal(scanned, expected)) {
        commit(s);
        result = scanned;
        ok = 1;
    } else {
        unscan(s);
        result = term_new_from_cstring("expected '");
        result = term_concat(result, expected);
        result = term_concat(result, term_new_from_cstring("' found '"));
        result = term_concat(result, scanned);
        result = term_concat(result, &APOS);
        ok = 0;
    }
}

void tamsin_alnum(struct scanner *s) {
    struct term *t = scan(s);
    if (t != &tamsin_EOF && isalnum(t->atom[0])) {
        commit(s);
        result = t;
        ok = 1;
    } else {
        unscan(s);
        result = term_new_from_cstring("expected alphanumeric, found '");
        result = term_concat(result, t);
        result = term_concat(result, &APOS);
        ok = 0;
    }
}

void tamsin_upper(struct scanner *s) {
    struct term *t = scan(s);
    if (t != &tamsin_EOF && isupper(t->atom[0])) {
        commit(s);
        result = t;
        ok = 1;
    } else {
        unscan(s);
        result = term_new_from_cstring("expected uppercase alphabetic, found '");
        result = term_concat(result, t);
        result = term_concat(result, &APOS);
        ok = 0;
    }
}

void tamsin_startswith(struct scanner *s, const char *str) {
    struct term *t = scan(s);
    if (t != &tamsin_EOF && t->atom[0] == str[0]) {
        commit(s);
        result = t;
        ok = 1;
    } else {
        unscan(s);
        result = term_new_from_cstring("expected '");
        result = term_concat(result, term_new_from_char(str[0]));
        result = term_concat(result, term_new_from_cstring("found '"));
        result = term_concat(result, t);
        result = term_concat(result, &APOS);
        ok = 0;
    }
}

struct term *tamsin_unquote(const struct term *q) {
    if (q->atom[0] == '"' || q->atom[0] == '\'') {
        return term_new(q->atom + 1, q->size - 2);
    }
    return term_new(q->atom, q->size);
}

struct term *tamsin_mkterm_r(struct term *t, const struct term *list) {
    if (term_atom_cstring_equal(list, "list") && list->subterms != NULL) {
        tamsin_mkterm_r(t, list->subterms->next->term);
        term_add_subterm(t, list->subterms->term);
    }
}

struct term *tamsin_mkterm(const struct term *atom, const struct term *list) {
    struct term *t = term_new(atom->atom, atom->size);
    tamsin_mkterm_r(t, list);
    return t;
}
