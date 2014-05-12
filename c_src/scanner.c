/*
 * Copyright (c)2014 Chris Pressey, Cat's Eye Technologies.
 * Distributed under a BSD-style license; see LICENSE for more information.
 */

#include "tamsin.h"

struct scanner *scanner_new(const char *buffer, size_t size) {
    struct scanner *scanner;

    scanner = malloc(sizeof(struct scanner));
    scanner->buffer = buffer;
    scanner->size = size;
    scanner->position = 0;
    scanner->reset_position = 0;
    scanner->engines = NULL;

    return scanner;
}

void scanner_byte_engine(void) {
}

void scanner_utf8_engine(void) {
}

#define UTF_8_LEN_2_MASK  0xe0    /* 0b11100000 */
#define UTF_8_LEN_2_BITS  0xc0    /* 0b11000000 */

#define UTF_8_LEN_3_MASK  0xf0    /* 0b11110000 */
#define UTF_8_LEN_3_BITS  0xe0    /* 0b11100000 */

#define UTF_8_LEN_4_MASK  0xf8    /* 0b11111000 */
#define UTF_8_LEN_4_BITS  0xf0    /* 0b11110000 */

const struct term *scan(struct scanner *s) {
    if (s->position >= s->size) {
        return &tamsin_EOF;
    }
    if (s->engines == NULL || s->engines->production == &scanner_utf8_engine) {
        char c = s->buffer[s->position];
        int len = 1;
        struct term *t;

        if ((c & UTF_8_LEN_2_MASK) == UTF_8_LEN_2_BITS) {
            len = 2;
        } else if ((c & UTF_8_LEN_3_MASK) == UTF_8_LEN_3_BITS) {
            len = 3;
        } else if ((c & UTF_8_LEN_4_MASK) == UTF_8_LEN_4_BITS) {
            len = 4;
        }

        t = term_new(s->buffer + s->position, len);
        s->position += len;
        /*term_fput(t, stderr);*/
        return t;
    } else if (s->engines->production == &scanner_byte_engine) {
        char c = s->buffer[s->position];

        s->position++;
        return term_new_from_char(c);
    } else {
        /*fprintf(stderr, "calling s->engines here\n");*/
        const struct term *save_result = result;
        int save_reset_position = s->reset_position;

        s->engines->production();
        s->reset_position = save_reset_position;

        if (!ok) {
            result = save_result;
            return &tamsin_EOF;
        } else {
            return result;
        }
    }
}

void unscan(struct scanner *s) {
    s->position = s->reset_position;
}

void commit(struct scanner *s) {
    s->reset_position = s->position;
}

struct engine *engine_new(void (*production)(void)) {
    struct engine *e = malloc(sizeof(struct engine));

    e->production = production;
    return e;
}

void scanner_push_engine(struct scanner *s, void (*production)(void)) {
    struct engine *e = engine_new(production);

    e->next = s->engines;
    s->engines = e;
}

void scanner_pop_engine(struct scanner *s) {
    /* struct engine *e = s->engines; */

    s->engines = s->engines->next;
    /* engine_free(e); */
}
