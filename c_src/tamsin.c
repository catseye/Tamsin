/*
 * Copyright (c)2014 Chris Pressey, Cat's Eye Technologies.
 * Distributed under a BSD-style license; see LICENSE for more information.
 */

#include "tamsin.h"

struct term APOS = {"'", 1, -1, NULL};

int tamsin_isupper(char c) {
    return (c >= 'A' && c <= 'Z');
}

int tamsin_isalpha(char c) {
    return (c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z');
}

int tamsin_isdigit(char c) {
    return (c >= '0' && c <= '9');
}

int tamsin_isalnum(char c) {
    return (c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') ||
           (c >= '0' && c <= '9');
}

void tamsin_eof(struct scanner *s) {
    const struct term *t = scan(s);
    unscan(s);
    if (t == &tamsin_EOF) {
        result = term_new("", 0);
        ok = 1;
    } else {
        result = term_new_from_cstring("expected EOF found '");
        result = term_concat(result, t);
        result = term_concat(result, &APOS);
        ok = 0;
    }
}

void tamsin_any(struct scanner *s) {
    const struct term *t = scan(s);
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
    const struct term *scanned = scan(s);
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
    const struct term *t = scan(s);
    if (t != &tamsin_EOF && tamsin_isalnum(t->atom[0])) {
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
    const struct term *t = scan(s);
    if (t != &tamsin_EOF && tamsin_isupper(t->atom[0])) {
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
    const struct term *t = scan(s);
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

const struct term *tamsin_unquote(const struct term *q,
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

const struct term *tamsin_equal(const struct term *l, const struct term *r) {
    if (term_equal(l, r)) {
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

const struct term *tamsin_mkterm(const struct term *atom,
                                 const struct term *list) {
    struct term *t = term_new(atom->atom, atom->size);
    tamsin_mkterm_r(t, list);
    return t;
}

const struct term *tamsin_reverse(const struct term *list, const struct term *sentinel) {
    const struct term *res = sentinel;
    const struct term *head = list;  /* save */

    while (list->subterms != NULL && term_atoms_equal(list, head)) {
        struct term *new = term_new(head->atom, head->size);
        
        /*term_fput(list, stderr);
        fprintf(stderr, "\n");*/

        term_add_subterm(new, res);
        term_add_subterm(new, list->subterms->term);
        res = new;
        if (list->subterms->next == NULL) {
            break;
        }
        list = list->subterms->next->term;
    }

    if (term_equal(list, sentinel)) {
        ok = 1;
        return res;
    } else {
        res = term_new_from_cstring("malformed list ");
        res = term_concat(res, term_flatten(head));
        ok = 0;
        return res;
    }
}

static int counter = 0;
static char buffer[80];
const struct term *tamsin_gensym(const struct term *base) {
    const struct term *t = term_flatten(base);

    counter++;
    /* snprintf(buffer, 79, "%d", counter); */
    sprintf(buffer, "%d", counter);
    t = term_concat(t, term_new_from_cstring(buffer));

    return t;
}

int hexdigit_to_int(char hd) {
    if (hd >= '0' && hd <= '9') return hd-'0';
    if (hd >= 'a' && hd <= 'f') return hd-'a' + 10;
    if (hd >= 'A' && hd <= 'F') return hd-'A' + 10;
    assert(0);
    return 0;
}

const struct term *tamsin_hexbyte(const struct term *high, const struct term *low) {
    const struct term *h = term_flatten(high);
    const struct term *l = term_flatten(low);
    int hi, lo;
    
    assert(h->size > 0);
    assert(l->size > 0);

    hi = hexdigit_to_int(h->atom[0]);
    lo = hexdigit_to_int(l->atom[0]);

    return term_new_from_char((char)(hi * 16 + lo));
}

/* uses same buffer as gensym because to do otherwise would be less awesome */
const struct term *tamsin_format_octal(const struct term *chr) {
    const struct term *t = term_flatten(chr);

    assert(t->size > 0);

    /* snprintf(buffer, 79, "%o", (unsigned char)t->atom[0]); */
    sprintf(buffer, "%o", (unsigned char)t->atom[0]);

    return term_new_from_cstring(buffer);
}

/* uses same buffer as gensym because to do otherwise would be less awesome */
const struct term *tamsin_length(const struct term *t) {
    t = term_flatten(t);

    /* snprintf(buffer, 79, "%lu", t->size); */
    sprintf(buffer, "%lu", t->size);

    return term_new_from_cstring(buffer);
}
