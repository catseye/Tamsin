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
    size_t size;
    int index;
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
struct term *term_new(const char *, size_t);

struct term *term_new_from_cstring(const char *);
struct term *term_new_from_char(char c);

struct term *term_new_variable(const char *, struct term *);

struct term *term_deep_copy(const struct term *);

/*
 * Modifies the given term.
 */
void term_add_subterm(struct term *, struct term *);

/*
 * Returns 1 if the atom portion of both terms is identical, otherwise 0.
 */
int term_atoms_equal(const struct term *, const struct term *);

/*
 * Returns 1 if the atom portion of term is identical to given C string, else 0.
 */
int term_atom_cstring_equal(const struct term *, const char *);

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
 * Given a possibly non-atom term, return an atom consisting of
 * contents of the given term flattened into an atom.
 *
 * The returned term is always newly allocated.
 */
struct term *term_flatten(const struct term *);

/*
 * Given a possibly non-atom term, return an atom consisting of
 * contents of the given term reprified into an atom.
 *
 * The returned term is always newly allocated.
 */
struct term *term_repr(const struct term *);

void term_fput(const struct term *, FILE *);

/*
 * ...
 */
int term_match(struct term *, struct term *);

/*
 * The third argument is an array of struct term *'s.  It will
 * be updated with bindings.
 */
int term_match_unifier(const struct term *, const struct term *,
                       const struct term **);

/*
 * This value is never (and should never be) exposed to Tamsin programs!
 * It should not be considered a kind of term, really.  That's just for
 * convenience in this implementation.
 */
extern struct term tamsin_EOF;

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
void tamsin_expect(struct scanner *, const struct term *);
void tamsin_alnum(struct scanner *);
void tamsin_upper(struct scanner *);
void tamsin_startswith(struct scanner *, const char *);
struct term *tamsin_unquote(const struct term *,
                            const struct term *, const struct term *);
struct term *tamsin_mkterm(const struct term *, const struct term *);
struct term *tamsin_equal(struct term *, struct term *);
struct term *tamsin_reverse(struct term *, struct term *);
struct term *tamsin_gensym(struct term *);
struct term *tamsin_hexbyte(struct term *, struct term *);
struct term *tamsin_format_octal(struct term *);
struct term *tamsin_length(struct term *);

int tamsin_isalpha(char);
int tamsin_isupper(char);
int tamsin_isdigit(char);
int tamsin_isalnum(char);

/* --------------------------------------------------------------- */
/* global state: result of last action */

extern int ok;
extern struct term *result;
