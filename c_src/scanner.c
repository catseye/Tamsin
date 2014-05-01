/*
 * Copyright (c)2014 Chris Pressey, Cat's Eye Technologies.
 * Distributed under a BSD-style license; see LICENSE for more information.
 */

#include "tamsin.h"

struct scanner *scanner_new(const char *buffer) {
    struct scanner *scanner;

    scanner = malloc(sizeof(struct scanner));
    scanner->buffer = buffer;
    scanner->position = 0;
    scanner->reset_position = 0;

    return scanner;
}

char scan(struct scanner *s) {
    char c = s->buffer[s->position];
    if (c == '\0') {
        return '\0';
    } else {
        s->position++;
        return c;
    }
};

void unscan(struct scanner *s) {
    s->position = s->reset_position;
}

void commit(struct scanner *s) {
    s->reset_position = s->position;
}
