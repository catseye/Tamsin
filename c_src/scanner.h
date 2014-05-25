/*
 * Copyright (c)2014 Chris Pressey, Cat's Eye Technologies.
 * Distributed under a BSD-style license; see LICENSE for more information.
 */

#ifndef TAMSIN_SCANNER_H
#define TAMSIN_SCANNER_H

#include "term.h"

/* -------------------------------------------------------- scanner */

struct engine {
    void (*production)(void);
    struct engine *next;
};

struct scanner {
    const char *buffer;
    size_t size;
    int position;
    int reset_position;
    struct engine *engines;
};

struct scanner *scanner_new(const char *, size_t);
const struct term *scan(struct scanner *);
void unscan(struct scanner *);
void commit(struct scanner *);
void scanner_push_engine(struct scanner *, void (*)(void));
void scanner_pop_engine(struct scanner *);
void scanner_byte_engine(void);
void scanner_utf8_engine(void);

/*
 * This value is never (and should never be) exposed to Tamsin programs!
 * It should not be considered a kind of term, really.  That's just for
 * convenience in this implementation.
 */
extern struct term tamsin_EOF;

#endif
