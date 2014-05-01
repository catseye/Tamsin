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
        result = new_term("EOF");
        ok = 1;
    } else {
        result = new_term("expected EOF found '");
        result = term_concat(result, new_term_from_char(c));
        result = term_concat(result, new_term("'"));
        ok = 0;
    }
}

void tamsin_any(struct scanner *s) {
    char c = scan(s);
    if (c == '\0') {
        unscan(s);
        result = new_term("expected any token, found EOF");
        ok = 0;
    } else {
        commit(s);
        result = new_term_from_char(c);
        ok = 1;
    }
}

void tamsin_expect(struct scanner *s, char *token) {
    char c = scan(s);
    if (c == token[0]) {
        commit(s);
        result = new_term_from_char(c);
        ok = 1;
    } else {
        unscan(s);
        result = new_term("expected '");
        result = term_concat(result, new_term(token));
        result = term_concat(result, new_term("' found '"));
        if (c == '\0') {
            result = term_concat(result, new_term("EOF'"));
        } else {
            result = term_concat(result, new_term_from_char(c));
            result = term_concat(result, new_term("'"));
        }
        ok = 0;
    }
};

void tamsin_alnum(struct scanner *s) {
    char c = scan(s);
    if (isalnum(c)) {
        commit(s);
        result = new_term_from_char(c);
        ok = 1;
    } else {
        unscan(s);
        result = new_term("expected alphanumeric, found '");
        result = term_concat(result, new_term_from_char(c));
        result = term_concat(result, new_term("'"));
        ok = 0;
    }
};
