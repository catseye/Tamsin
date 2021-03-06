/*
 * Copyright (c)2014 Chris Pressey, Cat's Eye Technologies.
 * Distributed under a BSD-style license; see LICENSE for more information.
 */

#ifndef TAMSIN_TAMSIN_H
#define TAMSIN_TAMSIN_H

#include "term.h"
#include "scanner.h"

/* -------------------------------------------------------- tamsin */

void tamsin_eof(struct scanner *);
void tamsin_any(struct scanner *);
void tamsin_expect(struct scanner *, const struct term *);
void tamsin_alnum(struct scanner *);
void tamsin_upper(struct scanner *);
void tamsin_startswith(struct scanner *, const char *);
const struct term *tamsin_unquote(const struct term *,
                                  const struct term *, const struct term *);
const struct term *tamsin_mkterm(const struct term *, const struct term *);
const struct term *tamsin_equal(const struct term *, const struct term *);
const struct term *tamsin_reverse(const struct term *, const struct term *);
const struct term *tamsin_gensym(const struct term *);
const struct term *tamsin_hexbyte(const struct term *, const struct term *);
const struct term *tamsin_format_octal(const struct term *);
const struct term *tamsin_length(const struct term *);

/*
 * Given a possibly non-atom term, return an atom consisting of
 * contents of the given term reprified into an atom.
 *
 * The returned term is NOT always newly allocated.
 */
const struct term *tamsin_repr(const struct term *);

int tamsin_isalpha(char);
int tamsin_isupper(char);
int tamsin_isdigit(char);
int tamsin_isalnum(char);

/* --------------------------------------------------------------- */
/* global state: result of last action */

extern int ok;
extern const struct term *result;

#endif
