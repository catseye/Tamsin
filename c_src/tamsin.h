/*
 * Copyright (c)2014 Chris Pressey, Cat's Eye Technologies.
 * Distributed under a BSD-style license; see LICENSE for more information.
 */

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* -------------------------------------------------------- terms */

/*
 * If `subterms` and `storing` are both NULL, this is an atom.
 * 
 * If `subterms` is non-NULL, this is a constructor.
 *
 * If `storing` field is non-NULL, this is a variable.
 * `storing` will point to a pointer to another term, which is the current
 * binding of this variable.  This other term may be a local variable in a C
 * function.  This will be used during expansion and pattern matching.
 *
 * It is not a legal term if both `storing` and `subterms` are non-NULL.
 *
 * In all cases, atom should not be NULL.
 */
struct term {
    char *atom;
    struct term *storing;
    struct term_list *subterms;
};

struct term_list {
    struct term *term;
    struct term_list *next;
};

/*
 * Creates a new "atom" term from the given character string.
 * The new term contains a dynamically allocated copy of the given string,
 *   so the given string may be freed after calling this.
 * Subterms may be added afterwards to turn it into a "constructor" term.
 * Segfaults if there is insufficient memory to allocate the term.
 */
struct term *term_new(const char *);

struct term *term_new_from_char(char c);

struct term *term_new_variable(const char *, struct term *);

/*
 * Modifies the given term.
 */
void add_subterm(struct term *, struct term *);

/*
 * Given the name of a variable, return the variable term of the
 * same name that is leftmost, uppermost in the given term.
 */
struct term *term_find_variable(const struct term *, const char *);

/*
 * Given two "atom" terms, return a new "atom" term consisting of the
 * text of the input terms concatenated together.
 */
struct term *term_concat(const struct term *, const struct term *);

/*
 * Given a possibly non-"atom" term, return a "atom" term consisting of
 * contents of the given term flattened into an atom.
 *
 * Note: for now, the returned term MAY OR MAY NOT be newly allocated.
 */
struct term *term_flatten(struct term *);

int term_match(struct term *, struct term *);

extern struct term tamsin_EOF;

/* -------------------------------------------------------- scanner */

struct engine {
    void (*production)(void);
    struct engine *next;
};

struct scanner {
    const char *buffer;
    int position;
    int reset_position;
    struct engine *engines;
};

struct scanner *scanner_new(const char *);
struct term *scan(struct scanner *);
void unscan(struct scanner *);
void commit(struct scanner *);
void scanner_push_engine(struct scanner *, void (*)(void));
void scanner_pop_engine(struct scanner *);
void scanner_byte_engine(void);
void scanner_utf8_engine(void);

/* -------------------------------------------------------- tamsin */

void tamsin_eof(struct scanner *);
void tamsin_any(struct scanner *);
void tamsin_expect(struct scanner *, const char *);
void tamsin_alnum(struct scanner *);
void tamsin_upper(struct scanner *);
void tamsin_startswith(struct scanner *, const char *);
struct term *tamsin_unquote(const struct term *);
struct term *tamsin_mkterm(const struct term *, const struct term *);


/* --------------------------------------------------------------- */
/* global state: result of last action */

extern int ok;
extern struct term *result;
