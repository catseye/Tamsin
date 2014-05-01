/*
 * Copyright (c)2014 Chris Pressey, Cat's Eye Technologies.
 * Distributed under a BSD-style license; see LICENSE for more information.
 */

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* terms */

struct term {
    char *atom;
    struct term_list *subterms;
};

struct term_list {
    struct term *term;
    struct term_list *next;
};

struct term *new_term(const char *);
struct term *new_term_from_char(char c);
void add_subterm(struct term *, struct term *);
struct term *term_concat(const struct term *, const struct term *);
struct term *term_flatten(struct term *);

/* scanner */

struct scanner {
    const char *buffer;
    int position;
    int reset_position;
};

struct scanner *scanner_new(const char *);
char scan(struct scanner *);
void unscan(struct scanner *);
void commit(struct scanner *);

/* tamsin */

void tamsin_eof(struct scanner *);
void tamsin_any(struct scanner *);
void tamsin_expect(struct scanner *, char *);
void tamsin_alnum(struct scanner *);

/* global state: result of last action */

extern int ok;
extern struct term *result;
