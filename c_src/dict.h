/*
 * Copyright (c)2014 Chris Pressey, Cat's Eye Technologies.
 * Distributed under a BSD-style license; see LICENSE for more information.
 */

#ifndef TAMSIN_DICT_H
#define TAMSIN_DICT_H

#include <stdlib.h>

struct dict {
    struct chain **bucket;
    size_t num_buckets;
};

/*
 * Create a new dictionary.
 * Since this is only used for hash-consing right now, there is only one.
 */
struct dict *dict_new(int);

/*
 * Retrieve a value from a dictionary, given its key, or NULL if it's not
 * there.
 */
const struct term *dict_fetch(struct dict *, const char *, size_t);

/*
 * Insert a value into a dictionary.
 */
void dict_store(struct dict *, const struct term *);

#endif
