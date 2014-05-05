
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

Meta-Language
-------------

(Also known, in their more practical incarnations, as "compiler-compilers"
or "parser generators".)

It is, because:
    
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

It isn't, because:

*   There is no requirement that any input be processed at all.

Programming Language
--------------------

It is, because:
    
*   Productions can have local variables.
*   Productions can call other productions (or themselves,
    recursively) with arguments, and they return a value:

        reverse(pair(H, T), A) = reverse(T, pair(H, A)).
        reverse(nil, A) = A.

*   It's Turing-complete.
*   It can be bootrapped.

It isn't, because:

*   The syntax is really geared to consuming input rather than calling
    functions.

Rubbish Lister
--------------

What does this even mean?  Well, there is that
[one famous rubbish lister](http://perl.com/) that we can use as an example
for now, until I come up with a better definition here.

It is, because:
    
*   There's more than one way to say it.
*   The same symbol means different things in different contexts
    (for example, `foo` might be either the name of a production, or an
    atomic term.)
*   Optomized (a bit) for problem-solving throwaway one-liners rather than
    large, engineered systems.
*   Anyone up for a game of golf?

It isn't, because:

*   Its syntax is possible to express in a form humans can understand.
