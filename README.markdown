Tamsin
======

Tamsin is a language somewhere between a programming language and a
meta-language (a language for defining languages.)  It also has some
characteristics reminiscent of unix shell programming and Erlang.
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
    Production ::= ProdName ["(" [Term {"," Term} ")" | "[" Expr0 "]"] "=" Expr0.
    Expr0 := Expr1 {("||" | "|") Expr1}.
    Expr1 := Expr2 {("&&" | "&") Expr2}.
    Expr2 := Expr3 ["using" ScannerSpec].
    Expr3 := Expr4 ["→" Variable].
    Expr4 := "(" Expr0 ")"
           | "[" Expr0 "]"
           | "{" Expr0 "}"
           | "set" Variable "=" Term
           | "return" Term
           | "fail" Term
           | "print" Term
           | "any"
           | "□"
           | LitToken
           | ProdName ["(" [Term {"," Term} ")"] ["@" Term].
    Term  := Term0.
    Term0 := Term1 {"•" Term1}.
    Term1 := Atom ["(" {Term0} ")"]
           | Variable.
    ScannerSpec = "☆" ("tamsin" | "char") | ProdName.
    Atom  := ("'" {any} "'" | { "a".."z" | "0".."9" }) using ☆char.
    Variable := ("A".."Z" { "a".."z" | "0".."9" }) using ☆char.
    ProdName ::= { "a".."z" | "0".."9" } using ☆char.

Examples
--------

    -> Tests for functionality "Parse Tamsin program"
    
    -> Functionality "Parse Tamsin program" is implemented by
    -> shell command "./src/tamsin.py parse %(test-body-file) | head -c 13"

Note that we're just concerned that it actually parsed; we don't care about
the representation of the internal AST.  So we truncate the output.

A Tamsin program consists of productions.  A production consists of a name
and a rule.  A rule may consist of a name of a production, or a terminal in
double quotes.

    | main = blerp.
    | blerp = "blerp".
    = ('PROGRAM', [

A rule may consist of two rules joined by `&`.

    | main = zeroes.
    | zeroes = "0" & zeroes.
    = ('PROGRAM', [

A rule may consist of two rules joined by `|`.

    | main = zeroes.
    | zeroes = "0" | "1".
    = ('PROGRAM', [

If you're too used to C or Javascript or `sh`, you can double up those symbols
to `&&` and `||`.  Note also that `&` has a higher precedence than `|`.

    | main = "0" && "1" || "2".
    = ('PROGRAM', [

A rule may consist of a bunch of other stuff.

    | main = zeroes.
    | zeroes(X) = ("0" & zeroes → E & return zero(E)) | return nil.
    = ('PROGRAM', [

    -> Tests for functionality "Intepret Tamsin program"
    
    -> Functionality "Intepret Tamsin program" is implemented by
    -> shell command "./src/tamsin.py run %(test-body-file) < %(test-input-file)"

When run, a Tamsin program parses the input.  A terminal expects a token
identical to it to be on the input.  If that expectation is met, it evaluates
to that token.  If not, it raises an error.

Note that input into a Tamsin program is first broken up into tokens as
specified by the lexical rules of Tamsin itself.  This is a little restrictive
for general use, but later on you'll see how to alter the scanner to something
more tuned for your needs.

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

And like any good language, you can print things.

    | main = print hello & return world.
    + ahoshoshohspohdphs
    = hello
    = world

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

    | main = "0" & return 1 | "1" & return 0.
    + 0
    = 1

    | main = "0" & return 1 | "1" & return 0.
    + 1
    = 0

    | main = "0" & return 1 | "1" & return 0.
    + 2
    ? expected '1' found '2'

Note that if the LHS of `|` fails, the RHS is tried at the position of
the stream that the LHS started on.  So basically, it's "backtracking".

    | ohone = "0" & "1".
    | ohtwo = "0" & "2".
    | main = ohone | ohtwo.
    + 0 2
    = 2

Alternatives can select code to be executed, basically.

    | main = aorb & print aorb | cord & print cord & return ok.
    | aorb = "a" & print ay | "b" & print bee.
    | cord = "c" & print see | eorf & print eorf.
    | eorf = "e" & print ee | f & print eff.
    + e
    = ee
    = eorf
    = cord
    = ok

If there is more input than we asked to parse, it still succeeds.

    | main = "sure" & "begorrah".
    + sure begorrah tis a fine day
    = begorrah

The symbol `□` may be used to match against the end of the input
(colloquially called "EOF".)

    | main = "sure" & "begorrah" & □.
    + sure begorrah
    = EOF

This is how you can error if there is extra input remaining.

    | main = "sure" & "begorrah" & □.
    + sure begorrah tis a fine day
    ? expected EOF found 'tis'

The end of the input is a virtual infinite stream of □'s.  You can match
as many as you like, and it continues to succeed.

    | main = "sure" & "begorrah" & □ & □ & □.
    + sure begorrah
    = EOF

The symbol `any` matches any token defined by the scanner.

    | main = any & any & any.
    + (@)
    = )

    | main = any & any & any.
    + words words words
    = words

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

In fact, the result of anything may be sent into a variable by `→`.  But
note that `→` has a higher precence than `&`.

    | main = ("0" | "1") → B & return itsa(B).
    + 0
    = itsa(0)

A `→` expression evaluates to the result placed in the variable.

    | main = (("0" | "1") → B) → Output & return itsa(Output).
    + 1
    = itsa(1)

This program accepts a pair of bits and outputs them as a list.

    | main = bit → A & bit → B & return pair(A, B).
    | bit = "0" | "1".
    + 1 0
    = pair(1, 0)

    | main = bit → A & bit → B & return pair(A, B).
    | bit = "0" | "1".
    + 0 1
    = pair(0, 1)

This program expects an infinite number of 0's.  It will be disappointed.

    | main = zeroes.
    | zeroes = "0" & zeroes.
    + 0 0 0 0 0
    ? expected '0' found 'EOF'

This program expects a finite number of 0's, and returns a term representing
how many it found.  It will not be disappointed.

    | main = zeroes.
    | zeroes = ("0" & zeroes → E & return zero(E)) | return nil.
    + 0 0 0 0
    = zero(zero(zero(zero(nil))))

This isn't the only way to set a variable.  You can also do so unconditionally.

    | main = eee.
    | eee = set E = whatever && set F = stuff && return pair(E ,F).
    + ignored
    = pair(whatever, stuff)

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
a sort.  It takes a term, which it uses as the failure message.

    | debug = return ok.
    | main = (debug & return walla | "0").
    + 0
    = walla

    | debug = fail notdebugging.
    | main = (debug & return walla | "0").
    + 0
    = 0

    | main = set E = 'Goodbye, world!' & fail E.
    + hsihdsihdsih
    ? Goodbye, world!

The rule `[FOO]` is a short form for `(FOO | return nil)`.

    | main = ["0"].
    + 0
    = 0

    | main = ["0"].
    + 
    = nil

So we can rewrite the "zeroes" example to be simpler:

    | main = zeroes.
    | zeroes = ["0" & zeroes → E & return zero(E)].
    + 0 0 0 0
    = zero(zero(zero(zero(nil))))

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
    | zeroes = set Z = nil & {"0" && set Z = zero(Z)} & return Z.
    + 0 0 0 0
    = zero(zero(zero(zero(nil))))

As mentioned, `"foo"` matches a literal token `foo` in the buffer.  But
what if you want to match something dynamic, something you have in a
variable?  You can do that with `«»`:

    | main = set E = foo & «E».
    + foo
    = foo

    | main = set E = foo & «E».
    + bar
    ? expected 'foo' found 'bar'

Aside
-----

OK!  So... here is a problem: if you haven't noticed yet,

*   what a rule consumes, is a string.
*   what a rule evaluates to, is a term.
*   the symbol `(` means something different in a rule (where it expresses
    precendence) than in a term (where it signifies the list of subterms.)
*   the symbol `foo` means something different in a rule (where it denotes
    a production) than in a term (where it is an atom.)

This is probably unacceptable.  Which syntax do we want to change?

    PRODUCTION = set V = foo & return ⟨atom V production⟩.

i.e. productions are distinguished from atoms and variables by being
all-caps.  Lists are distinguished from precedence by being ⟨ ⟩.

    production = set V = 'foo & return '(atom V production).

i.e. `'` acts a bit like quote, or rather quasi-quote, as Variables get
expanded.

    production = set V = :foo & return :smth(:atom Var :production).

i.e. atoms are prefixed with `:`, like Ruby, and terms are constructors
with a leading atom, like real terms and not like lists.

    production = set V = 「foo」 & return 「(atom Var anotheratom)」.

A funky, Japanese-influenced version of quote.  Nice, but really not suited
for this, quite.  Ditto ⟦these⟧.

Ah, well, it may not be a real problem, unless we want to make `return`
optional (which we do.)  Maybe, onto weirder stuff first.

Back to the examples
--------------------

A production may be called with arguments.

    | main = blerf(foo).
    | blerf(X) = return X.
    = foo

Note that this makes the «»-form more interesting.

    | main = bracketed(a) & bracketed(b) & return ok.
    | bracketed(X) = «X» & "stuff" & «X».
    + a stuff a b stuff b
    = ok

    | main = bracketed(a) & bracketed(b) & return ok.
    | bracketed(X) = «X» & "stuff" & «X».
    + a stuff a b stuff a
    ? expected 'b' found 'a'

We need to be able to test arguments somehow.  Well... how about we
pattern match the term?  Hahaha.

    | main = blerf(tree(a, b)).
    | blerf(tree(X, Y)) = return X.
    = a

    | main = blerf(c).
    | blerf(a) = return zzrk.
    | blerf(b) = return zon.
    | blerf(c) = return zzt.
    = zzt

    | main = blerf(d).
    | blerf(a) = return zzrk.
    | blerf(b) = return zon.
    | blerf(c) = return zzt.
    ? No 'blerf' production matched arguments [d]

Thus, we can write productions that recursively call themselves, and
terminate on the base case.

    | main = blerf(tree(tree(tree(a,b),c),d)).
    | blerf(tree(L,R)) = blerf(L).
    | blerf(Other) = return Other.
    = a

What does this get us?  I DON'T KNOW.  Oh, heck.  Let's parse a tree.

    | main = tree → T & rightmost(T).
    | tree = "tree" & "(" & tree → L & "," & tree → R & ")" & return tree(L, R)
    |      | "0" | "1" | "2".
    | rightmost(tree(L,R)) = rightmost(R).
    | rightmost(X) = return X.
    + tree(tree(0,1),tree(0,tree(1,2)))
    = 2

Implicit Buffer
---------------

OK, this section is mostly thoughts, until I come up with something.

Object-oriented languages sometimes have an "implicit self".  That means
when you say "foo", it's assumed (at least, to begin with,) to be a
method on the current object that is in context.

Tamsin, clearly, has an implicit buffer.  This is the buffer on which
scanning/parsing operations like `"tree"` operate.  When you call another
production from a production, that production you call gets the same
implicit buffer you were working on.  And `main` gets standard input as
its implicit buffer.

So, also clearly, there should be some way to alter the implicit buffer
when you call another production.

Here's a "problem": the implicit buffer is a string, and we don't have
strings in the data domain, we have terms.  This "problem" is easily
"solvable": we can stringify the term.  This is a terrible "solution",
but it lets us experiment further.

What's the syntax for this?  How about postfix `@`, because you're
pointing the production "at" some other text...

    | main = set T = tree(a,tree(b,c)) & tree @ T.
    | tree = "tree" & "(" & tree → L & "," & tree → R & ")" & return fwee(L, R)
    |      | "a" | "b" | "c".
    + doesn't matter
    = fwee(a, fwee(b, c))

This would be nicer if we had a syntax to put arbitrary text in an atom.
Hey, how about 「this is an atom」?  Hmmm...

For now, let's evaluate some backwards S-expressions.

Whew, finally got `{}` (while) working correctly.  Although, this result isn't
quite what I had in mind, but it does parse...

    | main = sexp.
    | sexp = symbol | list.
    | list = "(" &
    |        set L = nil &
    |        {sexp → S & set L = pair(S, L)} &
    |        ")" &
    |        return L.
    | symbol = "cons" | "head" | "tail" | "nil" | "a" | "b" | "c".
    + (cons (a (cons b nil)))
    = pair(pair(pair(nil, pair(b, pair(cons, nil))), pair(a, nil)), pair(cons, nil))

So let's write it in the less intuitive, recursive way:

    | main = sexp.
    | 
    | sexp = symbol | list.
    | list = "(" & listtail(nil).
    | listtail(L) = sexp → S & listtail(pair(S, L))
    |             | ")" & return L.
    | symbol = "cons" | "head" | "tail" | "nil" | "a" | "b" | "c".
    + (a b)
    = pair(b, pair(a, nil))

Reverser.  In Erlang this would be

    reverse([H|T], A) -> reverse(T, [H|A]).
    reverse([], A) -> A.

    | main = sexp → S & reverse(S, nil) → SR & return SR.
    | 
    | sexp = symbol | list.
    | list = "(" & listtail(nil).
    | listtail(L) = sexp → S & listtail(pair(S, L))
    |             | ")" & return L.
    | symbol = "cons" | "head" | "tail" | "nil" | "a" | "b" | "c".
    | 
    | reverse(pair(H, T), A) =
    |   reverse(T, pair(H, A)) → TR &
    |   return TR.
    | reverse(nil, A) =
    |   return A.
    + (a b)
    = pair(a, pair(b, nil))

But it's not deep.

    | main = sexp → S & reverse(S, nil) → SR & return SR.
    | 
    | sexp = symbol | list.
    | list = "(" & listtail(nil).
    | listtail(L) = sexp → S & listtail(pair(S, L))
    |             | ")" & return L.
    | symbol = "cons" | "head" | "tail" | "nil" | "a" | "b" | "c".
    | 
    | reverse(pair(H, T), A) =
    |   reverse(T, pair(H, A)) → TR &
    |   return TR.
    | reverse(nil, A) =
    |   return A.
    + (a (c b) b)
    = pair(a, pair(pair(b, pair(c, nil)), pair(b, nil)))

Deep reverser.

    | main = sexp → S & reverse(S, nil) → SR & return SR.
    | 
    | sexp = symbol | list.
    | list = "(" & listtail(nil).
    | listtail(L) = sexp → S & listtail(pair(S, L))
    |             | ")" & return L.
    | symbol = "cons" | "head" | "tail" | "nil" | "a" | "b" | "c".
    | 
    | reverse(pair(H, T), A) =
    |   reverse(H, nil) → HR &
    |   reverse(T, pair(HR, A)) → TR &
    |   return TR.
    | reverse(nil, A) =
    |   return A.
    | reverse(X, A) =
    |   return X.
    + (a (c b) b)
    = pair(a, pair(pair(c, pair(b, nil)), pair(b, nil)))

Finally, a little sexpr evaluator.

    | main = sexp → S & reverse(S, nil) → SR & eval(SR).
    | 
    | sexp = symbol | list.
    | list = "(" & listtail(nil).
    | listtail(L) = sexp → S & listtail(pair(S, L))
    |             | ")" & return L.
    | symbol = "cons" | "head" | "tail" | "nil" | "a" | "b" | "c".
    | 
    | head(pair(A, B)) = return A.
    | tail(pair(A, B)) = return B.
    | cons(A, B) = return pair(A, B).
    | 
    | eval(pair(head, pair(X, nil))) = eval(X) → R & head(R) → P & return P.
    | eval(pair(tail, pair(X, nil))) = eval(X) → R & tail(R) → P & return P.
    | eval(pair(cons, pair(A, pair(B, nil)))) =
    |    eval(A) → AE & eval(B) → BE & return pair(AE, BE).
    | eval(X) = return X.
    | 
    | reverse(pair(H, T), A) =
    |   reverse(H, nil) → HR &
    |   reverse(T, pair(HR, A)) → TR &
    |   return TR.
    | reverse(nil, A) =
    |   return A.
    | reverse(X, A) =
    |   return X.
    + (cons a b)
    = pair(a, b)

    | main = sexp → S & reverse(S, nil) → SR & eval(SR).
    | 
    | sexp = symbol | list.
    | list = "(" & listtail(nil).
    | listtail(L) = sexp → S & listtail(pair(S, L))
    |             | ")" & return L.
    | symbol = "cons" | "head" | "tail" | "nil" | "a" | "b" | "c".
    | 
    | head(pair(A, B)) = return A.
    | tail(pair(A, B)) = return B.
    | cons(A, B) = return pair(A, B).
    | 
    | eval(pair(head, pair(X, nil))) = eval(X) → R & head(R) → P & return P.
    | eval(pair(tail, pair(X, nil))) = eval(X) → R & tail(R) → P & return P.
    | eval(pair(cons, pair(A, pair(B, nil)))) =
    |    eval(A) → AE & eval(B) → BE & return pair(AE, BE).
    | eval(X) = return X.
    | 
    | reverse(pair(H, T), A) =
    |   reverse(H, nil) → HR &
    |   reverse(T, pair(HR, A)) → TR &
    |   return TR.
    | reverse(nil, A) =
    |   return A.
    | reverse(X, A) =
    |   return X.
    + (head (cons b a))
    = b

    | main = sexp → S & reverse(S, nil) → SR & eval(SR).
    | 
    | sexp = symbol | list.
    | list = "(" & listtail(nil).
    | listtail(L) = sexp → S & listtail(pair(S, L))
    |             | ")" & return L.
    | symbol = "cons" | "head" | "tail" | "nil" | "a" | "b" | "c".
    | 
    | head(pair(A, B)) = return A.
    | tail(pair(A, B)) = return B.
    | cons(A, B) = return pair(A, B).
    | 
    | eval(pair(head, pair(X, nil))) = eval(X) → R & head(R) → P & return P.
    | eval(pair(tail, pair(X, nil))) = eval(X) → R & tail(R) → P & return P.
    | eval(pair(cons, pair(A, pair(B, nil)))) =
    |    eval(A) → AE & eval(B) → BE & return pair(AE, BE).
    | eval(X) = return X.
    | 
    | reverse(pair(H, T), A) =
    |   reverse(H, nil) → HR &
    |   reverse(T, pair(HR, A)) → TR &
    |   return TR.
    | reverse(nil, A) =
    |   return A.
    | reverse(X, A) =
    |   return X.
    + (tail (tail (cons b (cons b a))))
    = a

In this one, we make the evaluator print out some of the steps it takes.

    | main = sexp → S & reverse(S, nil) → SR & eval(SR).
    | 
    | sexp = symbol | list.
    | list = "(" & listtail(nil).
    | listtail(L) = sexp → S & listtail(pair(S, L))
    |             | ")" & return L.
    | symbol = "cons" | "head" | "tail" | "nil" | "a" | "b" | "c".
    | 
    | head(pair(A, B)) = return A.
    | tail(pair(A, B)) = return B.
    | cons(A, B) = return pair(A, B).
    | 
    | eval(pair(head, pair(X, nil))) = eval(X) → R & head(R) → P & return P.
    | eval(pair(tail, pair(X, nil))) = eval(X) → R & tail(R) → P & return P.
    | eval(pair(cons, pair(A, pair(B, nil)))) =
    |    eval(A) → AE & eval(B) → BE &
    |    print y(AE, BE) & cons(AE, BE) → C & return C.
    | eval(X) = return X.
    | 
    | reverse(pair(H, T), A) =
    |   reverse(H, nil) → HR &
    |   reverse(T, pair(HR, A)) → TR &
    |   return TR.
    | reverse(nil, A) =
    |   return A.
    | reverse(X, A) =
    |   return X.
    + (cons (tail (cons b a)) (head (cons b a)))
    = y(b, a)
    = y(b, a)
    = y(a, b)
    = pair(a, b)

Implicit Scanner
----------------

Not only is there an implicit buffer, there is also, obviously, an implicit
scanner.  By default, this is the scanner for the Tamsin language.  But
you can change it!

### A prolix note on implementation ###

Traditionally, scanners for recursive descent parsers pre-emptively scan
the next token.  This was done because originally, parsers (for languages
like Pascal, say,) were distinctly one-pass beasts, reading the source code
off of a stream from disk (or maybe even from a tape), and you might need
to refer to the current token several times in the code and you don't want
to have to read it more than once.

This setup makes writing a parser with a "hot-swappable" scanner tricky,
because when we switch scanner, we have to deal with this "cached" token
somehow.  We could rewind the scanner by the length of the token (plus
the length of any preceding whitespace and comments), switch the scanner,
then scan again (by the new rules.)  But this is messy and error-prone.

Luckily, not many of us are reading files off tape these days, and we have
plenty of core, so it's no problem reading the whole file into memory.
In fact, I've seen it argued that the best way to write a scanner nowadays
is to `mmap()` the file.  We don't do this in the implementation of Tamsin,
but we do read the entire file into memory.

This makes the cache-the-next-token method less useful, and so we don't
do it.  Instead, we look for the next token only when we need it, and we
have a method `peek()` that returns what the next token would be, and we
don't cache this value.

There are a couple of other points about the scanner implementation.
A scanner only ever has one buffer (the entire string it's scanning); this
never changes over it's lifetime.  It provides methods for saving and
restoring its state, and it has a stack of "engines" which provide the
actual scanning logic.  In addition, there is only one interpreter object,
and it only has one scanner object during its lifetime.

### The scanners ###

The default scanner logic implements the scan rules for the Tamsin language.

    | main = cat.
    | cat = "cat" & return ok.
    + cat
    = ok

    | main = cat.
    | cat = "c" & "a" & "t" & return ok.
    + cat
    ? expected 'c' found 'cat'

You can select a different scanner for a rule with `using`.  Here we select
the builtin `☆char` scanner, which returns one character at a time.

    | main = cat using ☆char.
    | cat = "c" & "a" & "t" & return ok.
    + cat
    = ok

    | main = cat using ☆char.
    | cat = "cat" & return ok.
    + cat
    ? expected 'cat' found 'c'

You can mix two scanners in one production.  Note that the ☆tamsin scanner
doesn't consume spaces after a token, and that the ☆char scanner doesn't skip
spaces.

    | main = "dog" using ☆tamsin & ("c" & "a" & "t") using ☆char & return ok.
    + dog cat
    ? expected 'c' found ' '

But we can tell it to skip spaces...

    | main = "dog" using ☆tamsin
    |      & ({" "} & "c" & "a" & "t") using ☆char
    |      & return ok.
    + dog        cat
    = ok

Note that the scanner in force is lexically contained in the `using`.  Outside
of the `using`, scanning returns to whatever scanner was in force before the
`using`.

    | main = ("c" & "a" & "t" & " ") using ☆char & "dog".
    + cat dog
    = dog

On the other hand, variables set with one scanner can be accessed by another
scanner, as long as they're in the same production.

    | main = ("c" & "a" & "t" → G) using ☆char
    |      & ("dog" & return G) using ☆tamsin.
    + cat dog
    = t

**Note**: you need to be careful when using `using`!  Beware putting
`using` inside a rule that can fail, i.e. the LHS of `|` or inside a `{}`.
Because if it does fail and the interpreter reverts the scanner to its
previous state, its previous state may have been with a different scanning
logic.  The result may well be eurr.

Aside #2
--------

Well this is all very nice, very pretty I'm sure you'll agree, but it doesn't
hang together too well.  Figuration is easier than composition.  The thing is
that we still have these two domains, the domain of strings that we parse
and the domain of terms that we match.  We need to bring them closer together.
This section is just ideas for that.

One is that instead of, or alongside terms, we compose strings.

First, we put arbitrary text in an atom, with `「this syntax」`.  Then we allow
terms to be concatenated with `•`.  It looks real cool!  But also, it's kind
of annoying.  So we also allow `'this ' + 'syntax.'`.

So, something like:

    | main = return 「Hello, world!」.
    = Hello, world!

    | main = return 「fo go」 • 「od of」.
    + 9s9gs09gt8gibs
    = fo good of
    
    | main = {aorb → R & print R} & ".".
    | aorb = ("a" | "b") → C & return z • C.
    + a b a.
    = za
    = zb
    = za
    = .

    | main = set T = '' & {aorb → R & set T = T + R} & "." & return T.
    | aorb = ("a" | "b") → C & return z + C.
    + a b a.
    = zazbza

Then we no longer pattern-match terms.  They're just strings.  So we... we
parse them.  Here's a preview, and we'll get more serious about this further
below.

    | main = aorb → C & donkey(「fo go」 • C) → D & return D.
    | aorb = "a" | "b".
    | donkey["fo" & "goa"] = return yes.
    | donkey["fo" & "gob"] = return no.
    + a
    = yes

    | main = aorb → C & donkey('fo go' + C) → D & return D.
    | aorb = "a" | "b".
    | donkey["fo" & "goa"] = return yes.
    | donkey["fo" & "gob"] = return no.
    + b
    = no

Anyway, back to scanning
------------------------

Now that we can concatenate terms, we can probably write our own scanner.

    | main = scanner using ☆char.
    | scanner = {scan → A & print A} & ".".
    | scan = {" "} & ("-" & ">" & return 「->」 | "(" | ")" | "," | ";" | word).
    | word = letter → L & {letter → M & set L = L • M}.
    | letter = "a" | "b" | "c" | "d" | "e" | "f" | "g".
    + cabbage( bag , gaffe->fad ); bag(bagbag bag).
    = cabbage
    = (
    = bag
    = ,
    = gaffe
    = ->
    = fad
    = )
    = ;
    = bag
    = (
    = bagbag
    = bag
    = )
    = .

Indeed we can.

The next logical step would be to be able to say

    main = program using scanner.
    scanner = scan using ☆char.
    scan = {" "} & (...)
    program = "token" & ";" & "token" & ...

But we're not there yet.

Well, the best way to get there is to make that a test, see it fail, then
improve the implementation so that it passes,  Test-driven language design
for the win!  (But maybe not in all cases.  See my notes below...)

If this seems like an excessive number of tests, it's because I was chasing
a horribly deep bug for more than a day.  (They all pass now, though!  See
notes below.)

### Writing your own scanner ###

When you name a production in the program with `using`, that production
should return a token each time it is called.  We call this scanner a
"production-defined scanner" or just "production scanner".  In the
following, we use a production scanner based on the `scanner` production.
(But we use the Tamsin scanner to implement it, so it's not that interesting.)

    | main = program using scanner.
    | scanner = scan using ☆tamsin.
    | scan = "cat" | "dog".
    | program = "cat" & "dog".
    + cat dog
    = dog

Note that while it's conventional for a production scanner to return terms
similar to the strings it scanned, this is just a convention, and may be
subverted:

    | main = program using scanner.
    | scanner = scan using ☆tamsin.
    | scan = "cat" & return meow | "dog" & return woof.
    | program = "meow" & "woof".
    + cat dog
    = woof

We can also implement a production scanner with the ☆char scanner.  This is
more useful.

    | main = program using scanner.
    | scanner = scan using ☆char.
    | scan = "a" | "b" | "@".
    | program = "a" & "@" & "b" & return ok.
    + a@b
    = ok

If the production scanner fails to match the input text, it will return an EOF.
This is a little weird, but.  Well.  Watch this space.

    | main = program using scanner.
    | scanner = scan using ☆char.
    | scan = "a" | "b" | "@".
    | program = "a" & "@" & "b" & return ok.
    + x
    ? expected 'a' found 'EOF'

On the other hand, if the scanner understands all the tokens, but the parser
doesn't see the tokens it expects, you get the usual error.

    | main = program using scanner.
    | scanner = scan using ☆char.
    | scan = "a" | "b" | "@".
    | program = "a" & "@" & "b" & return ok.
    + b@a
    ? expected 'a' found 'b'

We can write a slightly more realistic scanner, too.

    | main = program using scanner.
    | scanner = scan using ☆char.
    | scan = "c" & "a" & "t" & return cat
    |      | "d" & "o" & "g" & return dog.
    | program = "cat" & "dog".
    + catdog
    = dog

Parsing using a production scanner ignores any extra text given to it,
just like the built-in parser.

    | main = program using scanner.
    | scanner = scan using ☆char.
    | scan = (
    |            "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |        ).
    | program = "cat" & "dog".
    + catdogfoobar
    = dog

Herein lie an excessive number of tests that I wrote while I was debugging.
Some of them will be cleaned up at a future point.

    | main = program using scanner.
    | scanner = scan using ☆char.
    | scan = {" "} & (
    |            "c" & "a" & "t" & return meow | "d" & "o" & "g" & return woof
    |        ).
    | program = "woof".
    + dog
    = woof

    | main = program using scanner.
    | scanner = scan using ☆char.
    | scan = {" "} & (
    |            "c" & "a" & "t" & return meow | "d" & "o" & "g" & return woof
    |        ).
    | program = "meow" | "woof".
    + cat
    = meow

    | main = program using scanner.
    | scanner = scan using ☆char.
    | scan = {" "} & (
    |            "c" & "a" & "t" & return meow | "d" & "o" & "g" & return woof
    |        ).
    | program = "meow" | "woof".
    + dog
    = woof

    | main = program using scanner.
    | scanner = scan using ☆char.
    | scan = (
    |            "c" & "a" & "t" & return meow | "d" & "o" & "g" & return woof
    |        ).
    | program = "meow" & "woof".
    + catdog
    = woof

    | main = program using scanner.
    | scanner = scan using ☆char.
    | scan = (
    |            "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |        ).
    | program = "cat" & "dog".
    + catdog
    = dog

    | main = program using scanner.
    | scanner = scan using ☆char.
    | scan = (
    |            "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |        ).
    | program = "cat" & print 1 &
    |           ("cat" & print 2 | "dog" & print 3) &
    |           "dog" & print 4 & return ok.
    + catcatdog
    = 1
    = 2
    = 4
    = ok

    | main = program using scanner.
    | scanner = scan using ☆char.
    | scan = (
    |            "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |        ).
    | program = "cat" & print 1 &
    |           ("cat" & print 2 | "dog" & print 3) &
    |           "dog" & print 4 & return ok.
    + catdogdog
    = 1
    = 3
    = 4
    = ok

    | main = program using scanner.
    | scanner = scan using ☆char.
    | scan = animal → A & return A.
    | animal = (
    |            "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |          ).
    | program = "cat" & print 1 &
    |           ("cat" & print 2 | "dog" & print 3) &
    |           "dog" & print 4 & return ok.
    + catdogdog
    = 1
    = 3
    = 4
    = ok

    | main = program using scanner.
    | scanner = scan using ☆char.
    | scan = animal → A & " " & return A.
    | animal = (
    |            "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |          ).
    | program = "cat" & print 1 &
    |           ("cat" & print 2 | "dog" & print 3) &
    |           "dog" & print 4 & return ok.
    + cat dog dog 
    = 1
    = 3
    = 4
    = ok

    | main = program using scanner.
    | scanner = scan using ☆char.
    | scan = animal → A & "," & return A.
    | animal = (
    |            "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |          ).
    | program = "cat" & print 1 &
    |           ("cat" & print 2 | "dog" & print 3) &
    |           "dog" & print 4 & return ok.
    + cat,dog,dog,
    = 1
    = 3
    = 4
    = ok

    | main = program using scanner.
    | scanner = scan using ☆char.
    | scan = animal → A & "-" & ">" & return A.
    | animal = (
    |            "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |          ).
    | program = "cat" & print 1 &
    |           ("cat" & print 2 | "dog" & print 3) &
    |           "dog" & print 4 & return ok.
    + cat->dog->dog->
    = 1
    = 3
    = 4
    = ok

    | main = program using scanner.
    | scanner = scan using ☆char.
    | scan = "X" & (
    |          "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |        ).
    | program = "cat" & "dog".
    + XcatXdog
    = dog

    | main = program using scanner.
    | scanner = scan using ☆char.
    | scan = " " & (
    |          "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |        ).
    | program = "cat" & "dog".
    +  cat dog
    = dog

    | main = program using scanner.
    | scanner = scan using ☆char.
    | scan = " " & animal.
    | animal = (
    |          "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |        ).
    | program = "cat" & "dog".
    +  cat dog
    = dog

    | main = program using scanner.
    | scanner = scan using ☆char.
    | scan = "(" & animal.
    | animal = (
    |          "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |        ).
    | program = "cat" & "dog".
    + (cat(dog
    = dog

    | main = program using scanner.
    | scanner = scan using ☆char.
    | scan = "(" & animal → A & ")" & return A.
    | animal = (
    |          "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |        ).
    | program = "cat" & "dog".
    + (cat)(dog)
    = dog

    | main = program using scanner.
    | scanner = scan using ☆char.
    | scan = " " & animal → A & ")" & return A.
    | animal = (
    |          "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |        ).
    | program = "cat" & "dog".
    +  cat) dog)
    = dog

    | main = program using scanner.
    | scanner = scan using ☆char.
    | scan = " " & animal → A & return A.
    | animal = (
    |            "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |          ).
    | program = "cat" & "dog".
    +  cat dog
    = dog

    | main = program using scanner.
    | scanner = scan using ☆char.
    | scan = " " & animal → A & return A.
    | animal = (
    |            "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |          ).
    | program = "cat" & ("dog" | "cat").
    +  cat dog
    = dog

    | main = program using scanner.
    | scanner = scan using ☆char.
    | scan = " " & animal → A & return A.
    | animal = (
    |            "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |          ).
    | program = "cat" & ("dog" | "cat").
    +  cat cat
    = cat

    | main = program using scanner.
    | scanner = scan using ☆char.
    | scan = " " & animal → A & return A.
    | animal = (
    |            "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |          ).
    | program = "cat" & ("cat" | "dog") & "dog".
    +  cat cat dog
    = dog

    | main = program using scanner.
    | scanner = (scan | return unknown) using ☆char.
    | scan = " " & animal → A & return A.
    | animal = (
    |            "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |          ).
    | program = "cat" & ("cat" | "dog") & "dog".
    +  cat dog dog
    = dog

    | main = program using scanner.
    | scanner = (scan | return unknown) using ☆char.
    | scan = " " & animal → A & return A.
    | animal = "c" & "a" & "t" & return cat
    |        | "d" & "o" & "g" & return dog
    |        | return unknown.
    | program = "cat" & ("cat" | "dog") & "dog".
    +  cat dog dog
    = dog

    | main = program using scanner.
    | scanner = (scan | return unknown) using ☆char.
    | scan = " " & animal → A & return A.
    | animal = (
    |            "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |            | "."
    |          ).
    | program = "cat" & ("cat" | "dog") & "dog" & ".".
    +  cat dog dog .
    = .

    | main = program using scanner.
    | scanner = (scan | return unknown) using ☆char.
    | scan = " " & animal → A & return A.
    | animal = (
    |            "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |          ).
    | program = "cat" & ("dog" | "cat") & "dog".
    +  cat cat dog
    = dog

    | main = program using scanner.
    | scanner = scan using ☆char.
    | scan = " " & animal → A & return A.
    | animal = (
    |            "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |          ).
    | program = "cat" & ("dog" | "cat") & "dog".
    +  cat dog dog
    = dog

    | main = program using scanner.
    | scanner = scan using ☆char.
    | scan = " " & animal → A & return A.
    | animal = (
    |            "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |          ).
    | program = "cat" & print 1 &
    |           ("cat" & print 2 | "dog" & print 3) &
    |           "dog" & print 4 & return ok.
    +  cat dog dog
    = 1
    = 3
    = 4
    = ok

    | main = program using scanner.
    | scanner = scan using ☆char.
    | scan = "X" & animal → A & return A.
    | animal = (
    |            "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |          ).
    | program = "cat" & print 1 &
    |           ("cat" & print 2 | "dog" & print 3) &
    |           "dog" & print 4 & return ok.
    + XcatXdogXdog
    = 1
    = 3
    = 4
    = ok

    | main = program using scanner.
    | scanner = scan using ☆char.
    | scan = "(" & animal → A & ")" & return A.
    | animal = (
    |            "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |          ).
    | program = "cat" & print 1 &
    |           ("cat" & print 2 | "dog" & print 3) &
    |           "dog" & print 4 & return ok.
    + (cat)(dog)(dog)
    = 1
    = 3
    = 4
    = ok

    | main = program using scanner.
    | scanner = scan using ☆char.
    | scan = {" "} & (
    |            "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |        ).
    | program = "cat" & "dog".
    + cat dog
    = dog

    | main = program using scanner.
    | scanner = scan using ☆char.
    | scan = {" "} & (
    |            "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |        ).
    | program = "cat" & print 1 &
    |           ("cat" & print 2 | "dog" & print 3) &
    |           "dog" & print 4 & return ok.
    + cat cat dog
    = 1
    = 2
    = 4
    = ok
    
    | main = program using scanner.
    | scanner = scan using ☆char.
    | scan = {" "} & (
    |            "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |        ).
    | program = "cat" & print 1 &
    |           ("cat" & print 2 | "dog" & print 3) &
    |           "dog" & print 4 & return ok.
    + cat dog dog
    = 1
    = 3
    = 4
    = ok

    | main = "cat" & print 1 &
    |        ("cat" & print 2 | "dog" & print 3) &
    |        "dog" & print 4 & return ok.
    + cat cat dog
    = 1
    = 2
    = 4
    = ok

    | main = "cat" & print 1 &
    |        ("cat" & print 2 | "dog" & print 3) &
    |        "dog" & print 4 & return ok.
    + cat dog dog
    = 1
    = 3
    = 4
    = ok

    | main = program using scanner.
    | scanner = scan using ☆char.
    | scan = {" "} & (
    |            "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |        ).
    | program = "cat" & ("cat" | "dog") & "dog".
    + cat cat cat
    ? expected 'dog' found 'cat'

    | main = program using scanner.
    | scanner = scan using ☆char.
    | scan = {" "} & (
    |            "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |        ).
    | program = "cat" & ("cat" | "dog") & "dog".
    + dog dog dog
    ? expected 'cat' found 'dog'

### Notes ###

Maybe test-driven language design *not* "for the win" in all cases; it's
excellent for evolving a design, but not so good for deep debugging.  I had
to actually write a dedicated test case which directly accessed the internals,
to find the problem.

This was only after refactoring the implementation two or three times.  One
of those times, I removed exceptions, so now the interpreter returns
`(success, result)` tuples, where `success` is a boolean, and propagates
parse errors itself.

We "raise" a parse error only in the `LITERAL` AST node.

We handle parse errors (backtrack) only in `OR` and `WHILE`, and in the
ProductionScannerEngine logic (to provide that EOF if the scanning production
failed.  This can happen even in `peek()` at the end of a string, even after
we've successfully parsed everything else.)

### More tests ###

A production scanner may contain an embedded `with` and use another
production scanner.

    | main = program using scanner1.
    | 
    | scanner1 = scan1 using ☆char.
    | scan1 = "a" | "b" | "c" | "(" & other & ")" & return list.
    | 
    | other = xyz using scanner2.
    | xyz = "1" & "1" | "1" & "2" | "2" & "3".
    | 
    | scanner2 = scan2 using ☆char.
    | scan2 = "x" & return 1 | "y" & return 2 | "z" & return 3.
    | program = "c" & "list" & "a".
    + c(xx)a
    = a

    | main = program using scanner1.
    | 
    | scanner1 = scan1 using ☆char.
    | scan1 = "a" | "b" | "c" | "(" & other & ")" & return list.
    | 
    | other = xyz using scanner2.
    | xyz = "1" & "1" | "1" & "2" | "2" & "3".
    | 
    | scanner2 = scan2 using ☆char.
    | scan2 = "x" & return 1 | "y" & return 2 | "z" & return 3.
    | program = "c" & "list" & "a".
    + c(yy)a
    ? expected 'list' found 'EOF'

Maybe an excessive number of minor variations on that...

    | main = program using scanner1.
    | 
    | scanner1 = scan1 using ☆char.
    | scan1 = "a" | "b" | "c" | "(" & xyz using scanner2 & ")" & return list.
    | 
    | xyz = "1" & "1" | "1" & "2" | "2" & "3".
    | 
    | scanner2 = scan2 using ☆char.
    | scan2 = "x" & return 1 | "y" & return 2 | "z" & return 3.
    | program = "c" & "list" & "a".
    + c(xx)a
    = a

    | main = program using scanner1.
    | 
    | scanner1 = scan1 using ☆char.
    | scan1 = "a" | "b" | "c" | "(" & {other} & ")" & return list.
    | 
    | other = xyz using scanner2.
    | xyz = "1" & "1" | "1" & "2" | "2" & "3".
    | 
    | scanner2 = scan2 using ☆char.
    | scan2 = "x" & return 1 | "y" & return 2 | "z" & return 3.
    | program = "c" & "list" & "a".
    + c(xxxyyzxy)a
    = a

    | main = program using scanner1.
    | 
    | scanner1 = scan1 using ☆char.
    | scan1 = "a" | "b" | "c" | "(" & {xyz using scanner2} & ")" & return list.
    | 
    | xyz = "1" & "1" | "1" & "2" | "2" & "3".
    | 
    | scanner2 = scan2 using ☆char.
    | scan2 = "x" & return 1 | "y" & return 2 | "z" & return 3.
    | program = "c" & "list" & "a".
    + c(xxxyyzxy)a
    = a

    | main = program using scanner1.
    | 
    | scanner1 = scan1 using ☆char.
    | scan1 = "a" | "b" | "c"
    |       | "(" & {xyz → R using scanner2} & ")" & return R.
    | 
    | xyz = "1" & "1" & return 11 | "1" & "2" & return 12 | "2" & "3" & return 23.
    | 
    | scanner2 = scan2 using ☆char.
    | scan2 = "x" & return 1 | "y" & return 2 | "z" & return 3.
    | program = "c" & ("11" | "12" | "23") → R & "a" & return R.
    + c(xxxyyzxy)a
    = 12

The production being applied with the production scanner can also switch
its own scanner.  It switches back to the production scanner when done.

    | main = program using scanner.
    | 
    | scanner = scan using ☆char.
    | scan = {" "} & set T = 「」 & {("a" | "b" | "c") → S & set T = T • S}.
    | 
    | program = "abc" & "cba" & "bac".
    + abc    cba bac
    = bac

    | main = program using scanner.
    | 
    | scanner = scan using ☆char.
    | scan = {" "} & set T = 「」 & {("a" | "b" | "c") → S & set T = T • S}.
    | 
    | program = "abc" & (subprogram using subscanner) & "bac".
    | 
    | subscanner = subscan using ☆char.
    | subscan = {" "} & set T = 「」 & {("s" | "t" | "u") → S & set T = T • S}.
    | 
    | subprogram = "stu" & "uuu".
    + abc    stu   uuu bac
    = bac

And now, back to "parse-patterns"
---------------------------------

Now that you can create scanners and parsers to your heart's desire, we
return to the reason you would even need to: terms vs. rules in the
"formal arguments" part of a production definition.

    | main = aorb → C & donkey(「fo go」 • C) → D & return D.
    | aorb = "a" | "b".
    | donkey["fo" & "goa"] = return yes.
    | donkey["fo" & "gob"] = return no.
    + a
    = yes

Having thought more about it, I think the easiest way to reconcile terms
and strings is to have terms be syntactic sugar for strings.  This is
already the case for ground terms, since `tree(a,b)` stringifies to the
same string as `「tree(a,b)」`.  It's when variables are involved where it
differs.  We would like some kind of quasi-quote such that even though
`「tree(A,b)」` → `tree(A,n)`, `«tree(A,b)»` → `tree(tree(x,y),b)` or
whatever.

Although, I still don't know.  The thing about terms is that they are
super-useful for intermediate representations — abstract syntax trees
and the like.  I've been thinking about some kind of compromise.  Which
is, currently, what we sort of have.  A Tamsin term doubles as a string,
for better or worse.  Mainly, we should sort out the properties of terms,
then.

Also todo:

*   dictionary values in variables?
*   non-printable characters in terms and such, e.g. "\n"
*   underscores in names
*   special form that consumes rest of input from the Tamsin source
