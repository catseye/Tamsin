#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* terms */

struct term {
    const char *atom;
    struct term_list *subterms;
};

struct term_list {
    struct term *term;
    struct term_list *next;
};

struct term *new_term(const char *);
void add_subterm(struct term *, struct term *);
void term_format_r(struct term *t);
char *term_format(struct term *t);

/* scanner */

struct scanner {
    char *buffer;
    int position;
    int reset_position;
};

char scan(struct scanner *);
void unscan(struct scanner *);
void commit(struct scanner *);

/* tamsin */

void tamsin_eof(struct scanner *);
void tamsin_any(struct scanner *);
void tamsin_expect(struct scanner *, char *);

/* global state: result of last action */

extern int ok;
extern struct term *result;
