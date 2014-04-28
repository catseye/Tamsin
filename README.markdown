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
    Expr2 := Expr3 ["with" Scanner].
    Expr3 := Expr4 ["→" Variable].
    Expr4 := "(" Expr0 ")"
           | "[" Expr0 "]"
           | "{" Expr0 "}"
           | "set" Variable "=" Term
           | "return" Term
           | "fail"
           | "print" Term
           | LitToken
           | ProdName ["(" [Term {"," Term} ")"] ["@" Term].
    Term  := Term0.
    Term0 := Term1 {"•" Term1}.
    Term1 := Atom ["(" {Term0} ")"]
           | Variable

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
specified by the gammar of Tamsin itself.  This is a little restrictive for
general use, but later on you'll see how to alter the scanner to something
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
    ? expected '0' found 'None'

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
you can change it!  Ideally, you could define your own scanner, but for
now, you'll only be able to select from the Tamsin scanner and a "raw"
scanner that only gives back characters.

As an implementation note: scanners for recursive descent parsers commonly
pre-emptively scan the next token.  So when we switch scanners, we'd have a
"leftover" token from the previous scanner, unless we deal with it in some
way.  The way we deal with it is to rewind the scanner by the length of
the last token scanned just before switching, then after switching, scan
again (by the new rules.)

    | main = cat.
    | cat = "cat" & return ok.
    + cat
    = ok

    | main = cat.
    | cat = "c" & "a" & "t" & return ok.
    + cat
    ? expected 'c' found 'cat'

    | main = cat with raw.
    | cat = "c" & "a" & "t" & return ok.
    + cat
    = ok

    | main = cat with raw.
    | cat = "cat" & return ok.
    + cat
    ? expected 'cat' found 'c'

You can mix two scanners in one production.  Note that the Tamsin scanner
doesn't consume spaces after a token, and that the raw scanner doesn't skip
spaces.

    | main = "dog" with tamsin & ("c" & "a" & "t") with raw & return ok.
    + dog cat
    ? expected 'c' found ' '

But we can make it skip spaces...

    | main = "dog" with tamsin & ({" "} & "c" & "a" & "t") with raw & return ok.
    + dog        cat
    = ok

Note that the scanner in force is lexically contained in the `with`.  Outside
of the `with`, scanning returns to whatever scanner was in force before the
`with`.

    | main = ("c" & "a" & "t" & " ") with raw & "dog".
    + cat dog
    = dog

But you need to be careful with `with`!  You should not put `with` inside
a rule that can fail, i.e. the LHS of `|` or inside a `{}`.  Because if it
does fail and the interpreter reverts the scanner to its previous state,
its previous state may have been a different scanner.  The result may well
be eurr.  I could make this a static error, but... for now, just remember
this and be careful.

Aside #2
--------

Well this is all very nice, very pretty I'm sure you'll agree, but it doesn't
hang together too well.  Figuration is easier than composition.  The thing is
that we still have these two domains, the domain of strings that we parse
and the domain of terms that we match.  We need to bring them closer together.
This section is just ideas for that.

One is that instead of, or alongside terms, we compose strings.

First, we put arbitrary text in an atom, with 「this syntax」.

Then we allow terms to be concatenated with •.

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

    | main = set T = 「」 & {aorb → R & set T = T • R} & "." & return T.
    | aorb = ("a" | "b") → C & return z • C.
    + a b a.
    = zazbza

Then we no longer pattern-match terms.  They're just strings.  So we... we
parse them.

Well, we can parse the putative syntax for this, anyway, but it's not
implemented yet.

    | main = aorb → C & donkey(「fo go」 • C) → D & return D.
    | aorb = "a" | "b".
    | donkey["fo" & "goa"] = return yes.
    | donkey["fo" & "gob"] = return no.
    + b
    ? No 'donkey' production matched arguments [fo gob]

Anyway, back to scanning
------------------------

Now that we can concatenate terms, we can probably write our own scanner.

    | main = scanner with raw.
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

    main = program with scanner.
    scanner = scan with raw.
    scan = {" "} & (...)
    program = "token" & ";" & "token" & ...

But we're not there yet.

Well, the best way to get there is to make that a test, see it fail, then
improve the implementation so that it passes,  Test-driven language design
for the win!

When you name a production in the program with `with`, that production
should return a token each time it is called.

    | main = program with scanner.
    | scanner = scan with tamsin.
    | scan = "cat" | "dog".
    | program = "cat" & "dog".
    + cat dog
    = dog

    | main = program with scanner.
    | scanner = scan with tamsin.
    | scan = "cat" & return meow | "dog" & return woof.
    | program = "meow" & "woof".
    + cat dog
    = woof

    | main = program with scanner.
    | scanner = scan with raw.
    | scan = {" "} & (
    |            "c" & "a" & "t" & return meow | "d" & "o" & "g" & return woof
    |        ).
    | program = "meow".
    + cat
    = meow

    | main = program with scanner.
    | scanner = scan with raw.
    | scan = {" "} & (
    |            "c" & "a" & "t" & return meow | "d" & "o" & "g" & return woof
    |        ).
    | program = "woof".
    + dog
    = woof

    | main = program with scanner.
    | scanner = scan with raw.
    | scan = {" "} & (
    |            "c" & "a" & "t" & return meow | "d" & "o" & "g" & return woof
    |        ).
    | program = "meow" | "woof".
    + cat
    = meow

    | main = program with scanner.
    | scanner = scan with raw.
    | scan = {" "} & (
    |            "c" & "a" & "t" & return meow | "d" & "o" & "g" & return woof
    |        ).
    | program = "meow" | "woof".
    + dog
    = woof

    | main = program with scanner.
    | scanner = scan with raw.
    | scan = (
    |            "c" & "a" & "t" & return meow | "d" & "o" & "g" & return woof
    |        ).
    | program = "meow" & "woof".
    + catdog
    = woof

    | main = program with scanner.
    | scanner = scan with raw.
    | scan = (
    |            "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |        ).
    | program = "cat" & "dog".
    + catdog
    = dog

    | main = program with scanner.
    | scanner = scan with raw.
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

    | main = program with scanner.
    | scanner = scan with raw.
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

    | main = program with scanner.
    | scanner = scan with raw.
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

    | main = program with scanner.
    | scanner = scan with raw.
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

    | main = program with scanner.
    | scanner = scan with raw.
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

    | main = program with scanner.
    | scanner = scan with raw.
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

    | main = program with scanner.
    | scanner = scan with raw.
    | scan = "X" & (
    |          "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |        ).
    | program = "cat" & "dog".
    + XcatXdog
    = dog

    | main = program with scanner.
    | scanner = scan with raw.
    | scan = " " & (
    |          "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |        ).
    | program = "cat" & "dog".
    +  cat dog
    = dog

    | main = program with scanner.
    | scanner = scan with raw.
    | scan = " " & animal.
    | animal = (
    |          "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |        ).
    | program = "cat" & "dog".
    +  cat dog
    = dog

    | main = program with scanner.
    | scanner = scan with raw.
    | scan = "(" & animal.
    | animal = (
    |          "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |        ).
    | program = "cat" & "dog".
    + (cat(dog
    = dog

    | main = program with scanner.
    | scanner = scan with raw.
    | scan = "(" & animal → A & ")" & return A.
    | animal = (
    |          "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |        ).
    | program = "cat" & "dog".
    + (cat)(dog)
    = dog

    | main = program with scanner.
    | scanner = scan with raw.
    | scan = " " & animal → A & ")" & return A.
    | animal = (
    |          "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |        ).
    | program = "cat" & "dog".
    +  cat) dog)
    = dog

    | main = program with scanner.
    | scanner = scan with raw.
    | scan = " " & animal → A & return A.
    | animal = (
    |            "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |          ).
    | program = "cat" & "dog".
    +  cat dog
    = dog

OK

    | main = program with scanner.
    | scanner = scan with raw.
    | scan = " " & animal → A & return A.
    | animal = (
    |            "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |          ).
    | program = "cat" & ("dog" | "cat").
    +  cat dog
    = dog

OK

    | main = program with scanner.
    | scanner = scan with raw.
    | scan = " " & animal → A & return A.
    | animal = (
    |            "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |          ).
    | program = "cat" & ("dog" | "cat").
    +  cat cat
    = cat

OK

    | main = program with scanner.
    | scanner = scan with raw.
    | scan = " " & animal → A & return A.
    | animal = (
    |            "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |          ).
    | program = "cat" & ("cat" | "dog") & "dog".
    +  cat cat dog
    = dog

NO.......

    | main = program with scanner.
    | scanner = scan with raw.
    | scan = " " & animal → A & return A.
    | animal = (
    |            "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |          ).
    | program = "cat" & ("cat" | "dog") & "dog".
    +  cat dog dog
    = dog

NO.......?

    | main = program with scanner.
    | scanner = scan with raw.
    | scan = " " & animal → A & return A.
    | animal = (
    |            "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |            | "."
    |          ).
    | program = "cat" & ("cat" | "dog") & "dog" & ".".
    +  cat dog dog .
    = .

OK

    | main = program with scanner.
    | scanner = scan with raw.
    | scan = " " & animal → A & return A.
    | animal = (
    |            "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |          ).
    | program = "cat" & ("dog" | "cat") & "dog".
    +  cat cat dog
    = dog

NO............

    | main = program with scanner.
    | scanner = scan with raw.
    | scan = " " & animal → A & return A.
    | animal = (
    |            "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |          ).
    | program = "cat" & ("dog" | "cat") & "dog".
    +  cat dog dog
    = dog

Notes:

    we raise TamsinParseError in 'LITERAL' only.
    we catch TamsinParseError in: 'OR', 'WITH', and 'WHILE'.
    we can rule out 'WHILE'.
    
    in `"c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog`,
    the `|` should catch any failures raised by any of c,a,t missing.

    indeed it seems like the problem is when the LHS of | matches
    and then there is something after it in the production
    
    OK so it looks like it *might* have to do with when
    ProductionScanner couldn't scan anything.  This could
    happen even in next_tok() at the end of a string, even after
    we've successfully parsed everything else.
    
    Will think about it.

Nope, does not like a space in front.

    @| main = program with scanner.
    @| scanner = scan with raw.
    @| scan = " " & animal → A & return A.
    @| animal = (
    @|            "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    @|          ).
    @| program = "cat" & print 1 &
    @|           ("cat" & print 2 | "dog" & print 3) &
    @|           "dog" & print 4 & return ok.
    @+  cat dog dog
    @= 1
    @= 3
    @= 4
    @= ok

Does not like an X in front either.

    @| main = program with scanner.
    @| scanner = scan with raw.
    @| scan = "X" & animal → A & return A.
    @| animal = (
    @|            "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    @|          ).
    @| program = "cat" & print 1 &
    @|           ("cat" & print 2 | "dog" & print 3) &
    @|           "dog" & print 4 & return ok.
    @+ XcatXdogXdog
    @= 1
    @= 3
    @= 4
    @= ok

Parens asking too much?

    @| main = program with scanner.
    @| scanner = scan with raw.
    @| scan = "(" & animal → A & ")" & return A.
    @| animal = (
    @|            "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    @|          ).
    @| program = "cat" & print 1 &
    @|           ("cat" & print 2 | "dog" & print 3) &
    @|           "dog" & print 4 & return ok.
    @+ (cat)(dog)(dog)
    @= 1
    @= 3
    @= 4
    @= ok

Solve this & I bet you solve the two following.

    | main = program with scanner.
    | scanner = scan with raw.
    | scan = {" "} & (
    |            "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |        ).
    | program = "cat" & "dog".
    + cat dog
    = dog

    @| main = program with scanner.
    @| scanner = scan with raw.
    @| scan = {" "} & (
    @|            "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    @|        ).
    @| program = "cat" & print 1 &
    @|           ("cat" & print 2 | "dog" & print 3) &
    @|           "dog" & print 4 & return ok.
    @+ cat cat dog
    @= 1
    @= 2
    @= 4
    @= ok
    @
    @| main = program with scanner.
    @| scanner = scan with raw.
    @| scan = {" "} & (
    @|            "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    @|        ).
    @| program = "cat" & print 1 &
    @|           ("cat" & print 2 | "dog" & print 3) &
    @|           "dog" & print 4 & return ok.
    @+ cat dog dog
    @= 1
    @= 3
    @= 4
    @= ok

Am I losing my mind?

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

No, eh?

    | main = program with scanner.
    | scanner = scan with raw.
    | scan = {" "} & (
    |            "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |        ).
    | program = "cat" & ("cat" | "dog") & "dog".
    + cat cat cat
    ? expected 'dog' found 'cat'

    | main = program with scanner.
    | scanner = scan with raw.
    | scan = {" "} & (
    |            "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |        ).
    | program = "cat" & ("cat" | "dog") & "dog".
    + dog dog dog
    ? expected 'cat' found 'dog'
