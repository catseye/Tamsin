/*
 * Copyright (c)2014 Chris Pressey, Cat's Eye Technologies.
 * Distributed under a BSD-style license; see LICENSE for more information.
 */

#include <assert.h>

#include "tamsin.h"

const struct term APOS = {"'", 1, -1, NULL};
const struct term BRA = { "(", 1, -1, NULL };
const struct term KET = { ")", 1, -1, NULL };
const struct term COMMA = { ", ", 2, -1, NULL };

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
        result = term_new_atom("", 0);
        ok = 1;
    } else {
        result = term_new_atom_from_cstring("expected EOF but found '");
        result = term_concat(result, t);
        result = term_concat(result, &APOS);
        ok = 0;
    }
}

void tamsin_any(struct scanner *s) {
    const struct term *t = scan(s);
    if (t == &tamsin_EOF) {
        unscan(s);
        result = term_new_atom_from_cstring("expected any token but found EOF");
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
        result = term_new_atom_from_cstring("expected '");
        result = term_concat(result, expected);
        if (scanned == &tamsin_EOF) {
            result = term_concat(result, term_new_atom_from_cstring("' but found EOF"));
        } else {
            result = term_concat(result, term_new_atom_from_cstring("' but found '"));
            result = term_concat(result, scanned);
            result = term_concat(result, &APOS);
        }
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
        result = term_new_atom_from_cstring("expected alphanumeric but found '");
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
        result = term_new_atom_from_cstring("expected uppercase but found '");
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
        result = term_new_atom_from_cstring("expected '");
        result = term_concat(result, term_new_atom_from_char(str[0]));
        result = term_concat(result, term_new_atom_from_cstring("...' but found '"));
        result = term_concat(result, t);
        result = term_concat(result, &APOS);
        ok = 0;
    }
}

const struct term *tamsin_unquote(const struct term *q,
                                  const struct term *l, const struct term *r) {
    int i;
    int good = 1;

    if (q->size < l->size + r->size) {
        good = 0;
    }
    if (good) {
        for (i = 0; i < l->size; i++) {
            if (q->atom[i] != l->atom[i]) {
                good = 0;
                break;
            }
        }
    }
    if (good) {
        for (i = 1; i <= r->size; i++) {
            if (q->atom[q->size - i] != r->atom[r->size - i]) {
                good = 0;
                break;
            }
        }
    }
    if (good) {
        ok = 1;
        return term_new_atom(q->atom + l->size, q->size - (l->size + r->size));
    } else {
        const struct term *result = term_new_atom_from_cstring("term '");
        result = term_concat(result, q);
        result = term_concat(result, term_new_atom_from_cstring(
            "' is not quoted with '"
        ));
        result = term_concat(result, l);
        result = term_concat(result, term_new_atom_from_cstring("' and '"));
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
        const struct term *result;
        
        result = term_new_atom_from_cstring("term '");
        result = term_concat(result, term_flatten(l));
        result = term_concat(result, term_new_atom_from_cstring(
            "' does not equal '"
        ));
        result = term_concat(result, term_flatten(r));
        result = term_concat(result, &APOS);
        ok = 0;
   
        return result;
    }
}

void tamsin_mkterm_r(struct termlist **tl, const struct term *list) {
    if (term_atom_cstring_equal(list, "list") && list->subterms != NULL) {
        tamsin_mkterm_r(tl, list->subterms->next->term);
        termlist_add_term(tl, list->subterms->term);
    }
}

const struct term *tamsin_mkterm(const struct term *atom,
                                 const struct term *list) {
    struct termlist *tl = NULL;

    tamsin_mkterm_r(&tl, list);

    return term_new_constructor(atom->atom, atom->size, tl);
}

const struct term *tamsin_reverse(const struct term *list, const struct term *sentinel) {
    const struct term *res = sentinel;
    const struct term *head = list;  /* save */

    while (list->subterms != NULL && term_atoms_equal(list, head)) {
        const struct term *new;
        struct termlist *tl = NULL;

        /*term_fput(list, stderr);
        fprintf(stderr, "\n");*/

        termlist_add_term(&tl, res);
        termlist_add_term(&tl, list->subterms->term);
        new = term_new_constructor(head->atom, head->size, tl);
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
        res = term_new_atom_from_cstring("malformed list ");
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
    t = term_concat(t, term_new_atom_from_cstring(buffer));

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

    return term_new_atom_from_char((char)(hi * 16 + lo));
}

/* uses same buffer as gensym because to do otherwise would be less awesome */
const struct term *tamsin_format_octal(const struct term *chr) {
    const struct term *t = term_flatten(chr);

    assert(t->size > 0);

    /* snprintf(buffer, 79, "%o", (unsigned char)t->atom[0]); */
    sprintf(buffer, "%o", (unsigned char)t->atom[0]);

    return term_new_atom_from_cstring(buffer);
}

/* uses same buffer as gensym because to do otherwise would be less awesome */
const struct term *tamsin_length(const struct term *t) {
    t = term_flatten(t);

    /* snprintf(buffer, 79, "%lu", t->size); */
    sprintf(buffer, "%lu", (unsigned long)t->size);

    return term_new_atom_from_cstring(buffer);
}

/** repr **/

/*
 * Returns the number of extra bytes we'll need to allocate to escape
 * this string.  0 indicates it does not need to be escaped.
 * control/high character = +3  (\xXX)
 * apos or backslash      = +1  (\\, \')
 */
static int escapes_needed(const char *text, size_t size) {
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

static int all_bareword(const char *text, size_t size) {
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

static const struct term *term_escape_atom(const struct term *t) {
    int needed;
    
    if (t->size == 0) {
        return term_new_atom("''", 2);
    }

    needed = escapes_needed(t->atom, t->size);

    if (needed > 0) {
        const struct term *r;
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

        r = term_new_atom("'", 1);
        r = term_concat(r, term_new_atom(buffer, t->size + needed));
        r = term_concat(r, term_new_atom("'", 1));
        free(buffer);

        return r;
    } else if (all_bareword(t->atom, t->size)) {
        /* TODO: can we eliminate this copy? */
        return term_new_atom(t->atom, t->size);
    } else {
        const struct term *r;

        r = term_new_atom("'", 1);
        r = term_concat(r, t);
        r = term_concat(r, term_new_atom("'", 1));

        return r;
    }
}

const struct term *tamsin_repr(const struct term *t) {
    struct termlist *tl;

    if (t->subterms == NULL) {  /* it's an atom */
        return term_escape_atom(t);
    } else {                           /* it's a constructor */
        const struct term *n;
        n = term_concat(term_escape_atom(t), &BRA);

        for (tl = t->subterms; tl != NULL; tl = tl->next) {
            n = term_concat(n, tamsin_repr(tl->term));
            if (tl->next != NULL) {
                n = term_concat(n, &COMMA);
            }
        }
        n = term_concat(n, &KET);
        return n;
    }
}
