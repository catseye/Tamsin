/*
 * Copyright (c)2014 Chris Pressey, Cat's Eye Technologies.
 * Distributed under a BSD-style license; see LICENSE for more information.
 */

#include "tamsin.h"

void tamsin_eof(struct scanner *s) {
    char c = scan(s);
    unscan(s);
    if (c == '\0') {
        result = new_term("EOF");
        ok = 1;
    } else {
        char t[100];
        sprintf(t, "expected EOF found '%c'", c);
        result = new_term(t);
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
        char t[2];
        commit(s);
        sprintf(t, "%c", c);
        result = new_term(t);
        ok = 1;
    }
}

void tamsin_expect(struct scanner *s, char *token) {
    char c = scan(s);
    if (c == token[0]) {
        commit(s);
        char s[10];
        strcpy(s, "a");
        s[0] = c;
        result = new_term(s);
        ok = 1;
    } else {
        unscan(s);
        char s[100];
        sprintf(s, "expected '%c' found '%c'", token[0], c);
        result = new_term(s);
        ok = 0;
    }
};
