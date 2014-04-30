/* an example of what I would hope a Tamsin->C compiler to produce.
   but this was written by hand. */

/* scanner */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

struct scanner {
    char *buffer;
    int position;
    int reset_position;
};

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

int consume(struct scanner *s, char *token) {
    char c = scan(s);
    //fprintf(stderr, "scanned '%c'\n", c);
    if (c == token[0]) {
        commit(s);
        //fprintf(stderr, "committed '%c'\n", c);
        return 1;
    } else {
        unscan(s);
        //fprintf(stderr, "rollbacked '%c'\n", c);
        return 0;
    }
};


/* terms */

struct term {
    const char *atom;
    struct term_list *subterms;
};

struct term_list {
    struct term *term;
    struct term_list *next;
};

struct term *new_term(const char *atom) {
    struct term *t;
    t = malloc(sizeof(struct term));
    t->atom = atom;
    t->subterms = NULL;
}

void add_subterm(struct term *term, struct term *subterm) {
    struct term_list *tl;
    tl = malloc(sizeof(struct term_list));
    tl->term = subterm;
    tl->next = term->subterms;
    term->subterms = tl;        
}



char fmtbuf[1000];  /* yeesh */

void term_format_r(struct term *t) {
    struct term_list *tl;

    strcat(fmtbuf, t->atom);
    if (t->subterms != NULL) {
        strcat(fmtbuf, "(");
        
        for (tl = t->subterms; tl != NULL; tl = tl->next) {
            term_format_r(tl->term);
            if (tl->next != NULL) {
                strcat(fmtbuf, ",");
            }
        }
        
        strcat(fmtbuf, ")");
    }
}

char *term_format(struct term *t) {
    strcpy(fmtbuf, "");
    term_format_r(t);
    return fmtbuf;
}

/* globals */

struct scanner * scanner;

/* result of last production */

int ok;
struct term *result;

/*
main = zeroes.
zeroes = ("0" & zeroes → E & return zero(E)) | return nil.
*/

/* gen'd protos */

void program_main(void);
void program_zeroes(void);

/* gen'd productions */

void program_main(void) {
    program_zeroes();
}

void program_zeroes(void) {
    struct term *E;

    tamsin_consume(scanner, "0");
    if (ok) {
        program_zeroes();
        E = result;
        if (ok) {
            struct term *temp = new_term("zero");
            add_subterm(temp, E);
            result = temp;
        }
    if (!ok) {
        struct term *temp = new_term("nil");
        result = temp;
        ok = 1;
    }
}

/* driver */

int main(int argc, char **argv) {
    
    scanner = malloc(sizeof(struct scanner));
    scanner->buffer = "0000";
    scanner->position = 0;
    scanner->reset_position = 0;

    ok = 0;
    result = NULL;

    tamsin_main();

    if (ok) {
        //fprintf(stderr, "done\n");
        fprintf(stdout, "%s\n", term_format(result));
        exit(0);
    } else {
        fprintf(stderr, "Error message\n");
        exit(1);
    }
}
