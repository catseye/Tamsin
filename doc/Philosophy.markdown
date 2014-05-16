Philosophy of Tamsin
====================

I suppose that's a rather heavy-handed word to use, "philosophy".  But
this is the document giving the _whys_ of Tamsin rather than the technical
points.

Why did you write Tamin?
------------------------

Basically, every time I see someone use a compiler-compiler like `yacc`
or a parser combinator library, part of me thinks, "Well why didn't
you just write a recursive-descent parser?  Recursive-descent parsers
are easy to write and they make for extremely pretty code!"
And what does a recursive-descent parser do?  It consumes input.  But
don't *all* algorithms consume input?  So why not have a language which
makes it easy to write recursive-descent parsers, and force all programs
to be written as recursive-descent parsers?  Then *all* code will be pretty!
(Yeah, sure, OK.)

Why is it/is it not a...
------------------------

### Meta-Language ###

(Also known, in their more practical incarnations, as "compiler-compilers"
or "parser generators".)

Tamsin is one, because:
    
*   The basic operations all map directly to combinators in BNF (or rather,
    Wirth's EBNF):
    *   `&` is sequencing
    *   `|` is alternation
    *   `[]` is sugar for alternation with the empty string
    *   `{}` is asteration
    *   `"foo"` is a terminal
    *   `foo` is a non-terminal
*   Using only these operations produces a sensible program — one which
    parses its input by the grammar so given.

Tamsin isn't one, because:

*   There is no requirement that any input be processed at all.

### Programming Language ###

Tamsin is one, because:

*   Productions can have local variables.
*   Productions can call other productions (or themselves, recursively) with
    arguments, and they return a value:

        reverse(pair(H, T), A) = reverse(T, pair(H, A)).
        reverse(nil, A) = A.

*   It's Turing-complete.
*   It can be, and in fact has been, bootstrapped.

Tamsin isn't one, because:

*   The syntax is really geared to consuming input rather than general
    programming.

### Rubbish Lister ###

What does this even mean?  Well, there is that
[one famous rubbish lister](http://perl.org/) that we can use as an example
for now, until I come up with a better definition here.

Tamsin is one, because:
    
*   There's more than one way to say it.
*   The same symbol means different things in different contexts
    (for example, `foo` might be either the name of a production, or an
    atomic term.)
*   Implicit this, implicit that.
*   Optomized (a bit) for problem-solving throwaway one-liners rather than
    large, engineered systems.
*   Anyone up for a game of golf?

Tamsin isn't one, because:

*   It's possible to express its syntax in a form that humans can understand.
*   In fact, it's possible to express its syntax in Tamsin.
    In fact, it's possible to bootstrap Tamsin — a Tamsin-to-C compiler has
    been written in Tamsin.  This is very un-rubbish-lister-ish.

Batteries Included
------------------

Are batteries included?  Or rather, _what_ batteries are included?  By strange
coincidence, the batteries that are included are almost exactly the ones
you'd expect to be useful in bootstrapping a Tamsin-to-C compiler:

*   `list` module — `reverse`, `append`, `member`, etc.
*   `tamsin_scanner` module
*   `tamsin_parser` module
*   `tamsin_analyzer` module
