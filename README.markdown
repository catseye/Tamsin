Tamsin
======

Tamsin is a language somewhere between a programming language and a
meta-language (a language for defining languages.)  It also has some
characteristics reminiscent of unix shell programming and Scheme.
(And Squishy2K.  And Chomsky Level 0 grammars.  And dioids.  And...)

Basically, every time I see someone use a compiler-compiler like `yacc`
or a parser combinator library, part of me thinks, "Well why didn't
you just write a recursive-descent parser?  Recursive-descent parsers
are easy to write and they make for extremely pretty code!"

And what does a recursive-descent parser do?  It consumes input.  But
don't *all* algorithms consume input?  So why not have a language which
makes it easy to write recursive-descent parsers, and force all programs
to be written as recursive-descent parsers?  Then all code will be pretty!
(Yeah, sure, OK.)

Where I'm going with this, I don't exactly know yet.  It is a work in
progress and will definitely change.

Grammar
-------

    Grammar ::= {Production "."}.
    Production ::= ProdName "=" Expr0.
    Expr0 := Expr1 {("||" | "|") Expr1}.
    Expr1 := Expr2 {("&&" | "&") Expr2}.
    Expr2 := "(" Expr0 ")"
           | "[" Expr0 "]"
           | "set" Variable "=" Term
           | "return" Term
           | "fail"
           | LitToken
           | ProdName ["→" Variable].

    Term := Atom
          | Variable
          | "(" {Term} ")".

Examples
--------

    -> Tests for functionality "Parse Tamsin program"
    
    -> Functionality "Parse Tamsin program" is implemented by
    -> shell command "./src/tamsin.py parse %(test-body-file)"

A Tamsin program consists of productions.  A production consists of a name
and a rule.  A rule may consist of a name of a production, or a terminal in
double quotes.

    | main = blerp.
    | blerp = "blerp".
    = ('PROGRAM', [('PROD', u'main', ('CALL', u'blerp', None)), ('PROD', u'blerp', ('LITERAL', u'blerp'))])

A rule may consist of two rules joined by `&`.

    | main = zeroes.
    | zeroes = "0" & zeroes.
    = ('PROGRAM', [('PROD', u'main', ('CALL', u'zeroes', None)), ('PROD', u'zeroes', ('AND', ('LITERAL', u'0'), ('CALL', u'zeroes', None)))])

A rule may consist of two rules joined by `|`.

    | main = zeroes.
    | zeroes = "0" | "1".
    = ('PROGRAM', [('PROD', u'main', ('CALL', u'zeroes', None)), ('PROD', u'zeroes', ('OR', ('LITERAL', u'0'), ('LITERAL', u'1')))])

If you're too used to C or Javascript or `sh`, you can double up those symbols
to `&&` and `||`.  Note also that `&` has a higher precedence than `|`.

    | main = "0" && "1" || "2".
    = ('PROGRAM', [('PROD', u'main', ('OR', ('AND', ('LITERAL', u'0'), ('LITERAL', u'1')), ('LITERAL', u'2')))])

A rule may consist of a bunch of other stuff.

    | main = zeroes.
    | zeroes = ("0" & zeroes → E & return (zero E)) | return nil.
    = ('PROGRAM', [('PROD', u'main', ('CALL', u'zeroes', None)), ('PROD', u'zeroes', ('OR', ('AND', ('AND', ('LITERAL', u'0'), ('CALL', u'zeroes', ('VAR', u'E'))), ('RETURN', ('LIST', [('ATOM', u'zero'), ('VAR', u'E')]))), ('RETURN', ('ATOM', u'nil'))))])

    | main = "0" & return one | "1" & return zero.
    = ('PROGRAM', [('PROD', u'main', ('OR', ('AND', ('LITERAL', u'0'), ('RETURN', ('ATOM', u'one'))), ('AND', ('LITERAL', u'1'), ('RETURN', ('ATOM', u'zero')))))])

    -> Tests for functionality "Intepret Tamsin program"
    
    -> Functionality "Intepret Tamsin program" is implemented by
    -> shell command "./src/tamsin.py run %(test-body-file) < %(test-input-file)"

When run, a Tamsin program parses the input.  A terminal expects a token
identical to it to be on the input.  If that expectation is met, it evaluates
to that token.  If not, it raises an error.

Note that input into a Tamsin program is first broken up into tokens as
specified by the gammar of Tamsin itself.  This is a little restrictive, and
is due to change at some point.

    | main = blerp.
    | blerp = "blerp".
    + blerp
    = blerp

    | main = blerp.
    | blerp = "blerp".
    + noodles
    ? expected 'blerp' found 'noodles'

Well, actually it doesn't have to look at its input.  The `return` keyword
forces evaluation to result in a particular value.  This program outputs 'blerp'
no matter what the input is.

    | main = blerp.
    | blerp = return blerp.
    + fadda wadda badda kadda nadda sadda hey
    = blerp

    | main = return blerp.
    + foo
    + foo
    + foo 0 0 0 0 0
    = blerp

But back to parsing.  The `&` operator processes its left-hand side on the
input, then the right-hand side.  It returns the result of its RHS.  But if
the LHS fails, the whole thing fails.

    | main = "sure" & "begorrah".
    + sure begorrah
    = begorrah

    | main = "sure" & "begorrah".
    + sure milwaukee
    ? expected 'begorrah' found 'milwaukee'

    | main = "sure" & "begorrah".
    + sari begorrah
    ? expected 'sure' found 'sari'

The `|` operator processes its left-hand side and returns the result of
that — unless it fails, in which case it processes its right-hand side
and returns the result of that.  For example, this program accepts `0` or
`1` but nothing else.

    | main = "0" | "1".
    + 0
    = 0

    | main = "0" | "1".
    + 1
    = 1

    | main = "0" | "1".
    + 2
    ? expected '1' found '2'

Using `return` described above, this program accepts 0 or 1 and evaluates
to the opposite.

    | main = "0" & return one | "1" & return zero.
    + 0
    = one

    | main = "0" & return one | "1" & return zero.
    + 1
    = zero

    | main = "0" & return one | "1" & return zero.
    + 2
    ? expected '1' found '2'

Note that if the LHS of `|` fails, the RHS is tried at the position of
the stream that the LHS started on.  So basically, it's "backtracking".

    | ohone = "0" & "1".
    | ohtwo = "0" & "2".
    | main = ohone | ohtwo.
    + 0 2
    = 2

When a production is called, the result that it evaluates to may be stored
in a variable.  Variables are local to the production.

    | main = blerp → B & return B.
    | blerp = "blerp".
    + blerp
    = blerp

Variables must be capitalized.

    | main = blerp → b & return b.
    | blerp = "blerp".
    ? Expected variable

This program accepts a pair of bits and outputs them as a list.

    | main = bit → A & bit → B & return (A B).
    | bit = "0" | "1".
    + 1 0
    = (1 0)

    | main = bit → A & bit → B & return (A B).
    | bit = "0" | "1".
    + 0 1
    = (0 1)

This program expects an infinite number of 0's.  It will be disappointed.

    | main = zeroes.
    | zeroes = "0" & zeroes.
    + 0 0 0 0 0
    ? expected '0' found 'None'

This program expects a finite number of 0's, and returns a term representing
how many it found.  It will not be disappointed.
    
    | main = zeroes.
    | zeroes = ("0" & zeroes → E & return (zero E)) | return nil.
    + 0 0 0 0
    = (zero (zero (zero (zero nil))))

This isn't the only way to set a variable.  You can also do so unconditionally.

    | main = eee.
    | eee = set E = whatever && set F = stuff && return (E F).
    + ignored
    = (whatever stuff)

And note that variables are subject to backtracking, too; if a variable is
set while parsing something that failed, it is no longer set in the `|`
alternative.

    | main = set E = original &
    |          (set E = changed && "0" && "1" | "0" && "2") &
    |        return E.
    + 0 1
    = changed

    | main = set E = original &
    |          (set E = changed && "0" && "1" | "0" && "2") &
    |        return E.
    + 0 2
    = original

The rule `fail` always fails.  This lets you establish global flags, of
a sort.

    | debug = return ok.
    | main = (debug & return walla | "0").
    + 0
    = walla

    | debug = fail.
    | main = (debug & return walla | "0").
    + 0
    = 0

The rule `[FOO]` is a short form for `(FOO | return nil)`.

    | main = ["0"].
    + 0
    = 0

    | main = ["0"].
    + 
    = nil

So we can rewrite the "zeroes" example to be simpler:

    | main = zeroes.
    | zeroes = ["0" & zeroes → E & return (zero E)].
    + 0 0 0 0
    = (zero (zero (zero (zero nil))))

The rule `{FOO}` is what it is in EBNF, and/or a while loop.  Like `[]`,
we don't strictly need it, because we could just write it as recursive
BNF.  But it's handy.  Like while loops are handy.  It returns the result
of the last successful rule applied, or `nil` if none were successful.

    | main = {"0"}.
    + 0 0 0 0
    = 0

    | main = {"0"}.
    + 1 2 3 4
    = nil

Backtracking applies to `{}` too.

    | zeroesone = {"0"} & "1".
    | zeroestwo = {"0"} & "2".
    | main = zeroesone | zeroestwo.
    + 0 0 0 0 0 2
    = 2

So we can rewrite the "zeroes" example to be even... I hesistate to use
the word "simpler", but we can... write it differently.

    | main = zeroes.
    | zeroes = set Z = nil & {"0" && set Z = (zero Z)} & return Z.
    + 0 0 0 0
    = (zero (zero (zero (zero nil))))
