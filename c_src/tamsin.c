/*
 * Copyright (c)2014 Chris Pressey, Cat's Eye Technologies.
 * Distributed under a BSD-style license; see LICENSE for more information.
 */

#include "tamsin.h"

#include <ctype.h>

void tamsin_eof(struct scanner *s) {
    char c = scan(s);
    unscan(s);
    if (c == '\0') {
        result = term_new("EOF");
        ok = 1;
    } else {
        result = term_new("expected EOF found '");
        result = term_concat(result, term_new_from_char(c));
        result = term_concat(result, term_new("'"));
        ok = 0;
    }
}

void tamsin_any(struct scanner *s) {
    char c = scan(s);
    if (c == '\0') {
        unscan(s);
        result = term_new("expected any token, found EOF");
        ok = 0;
    } else {
        commit(s);
        result = term_new_from_char(c);
        ok = 1;
    }
}

void tamsin_expect(struct scanner *s, const char *token) {
    char c = scan(s);
    if (c == token[0]) {
        commit(s);
        result = term_new_from_char(c);
        ok = 1;
    } else {
        unscan(s);
        result = term_new("expected '");
        result = term_concat(result, term_new(token));
        result = term_concat(result, term_new("' found '"));
        if (c == '\0') {
            result = term_concat(result, term_new("EOF'"));
        } else {
            result = term_concat(result, term_new_from_char(c));
            result = term_concat(result, term_new("'"));
        }
        ok = 0;
    }
}

void tamsin_alnum(struct scanner *s) {
    char c = scan(s);
    if (isalnum(c)) {
        commit(s);
        result = term_new_from_char(c);
        ok = 1;
    } else {
        unscan(s);
        result = term_new("expected alphanumeric, found '");
        result = term_concat(result, term_new_from_char(c));
        result = term_concat(result, term_new("'"));
        ok = 0;
    }
}

void tamsin_upper(struct scanner *s) {
    char c = scan(s);
    if (isupper(c)) {
        commit(s);
        result = term_new_from_char(c);
        ok = 1;
    } else {
        unscan(s);
        result = term_new("expected uppercase alphabetic, found '");
        result = term_concat(result, term_new_from_char(c));
        result = term_concat(result, term_new("'"));
        ok = 0;
    }
}

void tamsin_startswith(struct scanner *s, const char *str) {
    char c = scan(s);
    if (c == str[0]) {
        commit(s);
        result = term_new_from_char(c);
        ok = 1;
    } else {
        unscan(s);
        result = term_new("expected '");
        result = term_concat(result, term_new_from_char(str[0]));
        result = term_concat(result, term_new("found '"));
        result = term_concat(result, term_new_from_char(c));
        result = term_concat(result, term_new("'"));
        ok = 0;
    }
}


struct term *tamsin_unquote(const struct term *q) {
    if (q->atom[0] == '"' || q->atom[1] == '\'') {
        char *s = strdup(q->atom);
        s[strlen(s)-1] = '\0';
        return term_new(s+1);
    }
    return term_new(q->atom);
}

struct term *tamsin_mkterm_r(struct term *t, const struct term *list) {
    if (!strcmp(list->atom, "list") && list->subterms != NULL) {
        tamsin_mkterm_r(t, list->subterms->next->term);
        term_add_subterm(t, list->subterms->term);
    }
}

struct term *tamsin_mkterm(const struct term *atom, const struct term *list) {
    struct term *t = term_new(atom->atom);
    tamsin_mkterm_r(t, list);
    return t;
}
