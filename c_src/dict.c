#include <assert.h>
#include <stdlib.h>

#include "term.h"

#include "dict.h"

struct chain {
    struct chain *next;
    const struct term *value;
};

struct dict *dict_new(int num_buckets) {
    struct dict *d;
    int i;

    d = malloc(sizeof(struct dict));
    d->num_buckets = num_buckets;
    d->bucket = malloc(sizeof(struct chain *) * d->num_buckets);
    for (i = 0; i < d->num_buckets; i++) {
        d->bucket[i] = NULL;
    }

    return d;
}

/*** UTILITIES ***/

/*
 * Hash function, taken from "Compilers: Principles, Techniques, and Tools"
 * by Aho, Sethi, & Ullman (a.k.a. "The Dragon Book", 2nd edition.)
 */
static size_t hashpjw(const char *key, size_t key_size, size_t table_size) {
    int i;
    unsigned long int h = 0, g;

    for (i = 0; i < key_size; i++) {
        h = (h << 4) + (key[i]);
        if ((g = h & 0xf0000000)) {
            h = (h ^ (g >> 24)) ^ g;
        }
    }

    return h % table_size;
}

/*
 * Create a new chain for a bucket (not called directly by client code.)
 */
static struct chain *
chain_new(const struct term *value)
{
    struct chain *c = malloc(sizeof(struct chain));

    c->next = NULL;
    c->value = value;

    return c;
}

/*
 * Locate the bucket number a particular key would be located in, and the
 * chain link itself if such a key exists (or NULL if it could not be found.)
 */
static void
dict_locate(struct dict *d, const char *key, size_t key_size,
	    size_t *b_index, struct chain **c)
{
    *b_index = hashpjw(key, key_size, d->num_buckets);
    for (*c = d->bucket[*b_index]; *c != NULL; *c = (*c)->next) {
        if ((*c)->value->size == key_size &&
            memcmp(key, (*c)->value->atom, key_size) == 0)
            break;
    }
}

/*** OPERATIONS ***/

const struct term *
dict_fetch(struct dict *d, const char *key, size_t key_size)
{
    struct chain *c;
    size_t i;
    
    dict_locate(d, key, key_size, &i, &c);

    return c != NULL ? c->value : NULL;
}

void
dict_store(struct dict *d, const struct term *t)
{
    struct chain *c;
    size_t i;
    
    dict_locate(d, t->atom, t->size, &i, &c);
    if (c == NULL) {
        /* Chain does not exist, add a new one. */
        c = chain_new(t);
        c->next = d->bucket[i];
        d->bucket[i] = c;
    } else {
        assert("term already hash consed" == NULL);
        /* Chain already exists, replace the value. */
        c->value = t;
    }
}
