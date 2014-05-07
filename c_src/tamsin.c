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

struct term *tamsin_unquote(const struct term *q,
                            const struct term *l, const struct term *r) {
    if (q->size < 1 || l->size != 1 || r->size != 1) {
        struct term *result = term_new_from_cstring("bad terms for unquote");
        ok = 0;
        return result;
    }
    if (q->atom[0] == l->atom[0] && q->atom[q->size-1] == r->atom[0]) {
        ok = 1;
        return term_new(q->atom + 1, q->size - 2);
    } else {
        struct term *result = term_new_from_cstring("term '");
        result = term_concat(result, q);
        result = term_concat(result, term_new_from_cstring(
            "' is not quoted with '"
        ));
        result = term_concat(result, l);
        result = term_concat(result, term_new_from_cstring("' and '"));
        result = term_concat(result, r);
        result = term_concat(result, &APOS);
        ok = 0;
        return result;
    }
}

struct term *tamsin_equal(struct term *l, struct term *r) {
    if (term_match(l, r)) {
        ok = 1;
        return l;
    } else {
        struct term *result;
        
        result = term_new_from_cstring("term '");
        result = term_concat(result, term_flatten(l));
        result = term_concat(result, term_new_from_cstring(
            "' does not equal '"
        ));
        result = term_concat(result, term_flatten(r));
        result = term_concat(result, &APOS);
        ok = 0;
   
        return result;
    }
}

void tamsin_mkterm_r(struct term *t, const struct term *list) {
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

struct term *tamsin_reverse(struct term *list, struct term *sentinel) {
    struct term *result = sentinel;
    const struct term *head = list;  /* save */

    while (list->subterms != NULL && term_atoms_equal(list, head)) {
        struct term *new = term_new(head->atom, head->size);
        
        /*term_fput(list, stderr);
        fprintf(stderr, "\n");*/

        term_add_subterm(new, result);
        term_add_subterm(new, list->subterms->term);
        result = new;
        if (list->subterms->next == NULL) {
            break;
        }
        list = list->subterms->next->term;
    }

    if (term_match(list, sentinel)) {
        ok = 1;
        return result;
    } else {
        struct term *result = term_new_from_cstring("malformed list ");
        result = term_concat(result, term_flatten(head));
        ok = 0;
        return result;
    }
}
