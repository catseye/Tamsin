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

void tamsin_expect(struct scanner *s, char *token) {
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
};

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
};
