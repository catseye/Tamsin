The Tamsin Language Specification
=================================

This document is a **work in progress**.

    -> Tests for functionality "Intepret Tamsin program"
    
    -> Functionality "Intepret Tamsin program" is implemented by
    -> shell command "bin/tamsin run %(test-body-file) < %(test-input-file)"

Fundaments
----------

A Tamsin program consists of one or more productions.  A production consists
of a name and a rule.  Among other things, a rule may be a "non-terminal",
in which case it consists of the name of a production, or a "terminal",
in which case it is a literal string in double-quotes (or one of a number
of other things we'll get to in a moment.)

When run, a Tamsin program processes its input.  It starts at the production
named `main`, and evaluates its rule.  A non-terminal in a rule "calls" the
production of that name in the program.  A terminal in a a rule expects a token
identical to it to be on the input.  If that expectation is met, it evaluates
to that token.  If not, it raises an error.  The final result of evaluating a
Tamsin program is sent to its output.

(If it makes it easier to think about, consider "its input" to mean "stdin",
and "token" to mean "character"; so the terminal `"x"` is a command that either
reads the character `x` from stdin and returns it (whence it is printed to
stdout by the main program), or errors out if it read something else.
Or, thinking about it from the other angle, we have here the rudiments for
defining a grammar for parsing a trivial language.)

    | main = blerf.
    | blerf = "p".
    + p
    = p

    | main = blerf.
    | blerf = "p".
    + k
    ? expected 'p' found 'k'

A Tamsin program only looks at its input when evaluating a terminal.  A
rule may also consist of the keyword `return`, followed a term; this expression
forces the entire production to evaluates to that term.

So, the following program always outputs `blerp`, no matter what the input is.

    | main = return blerp.
    + fadda wadda badda kadda nadda sadda hey
    = blerp

Note that in the following, `blerp` refers to the production named "blerp"
in one place, and in the other place, it refers to a term which is basically
the literal string `blerp`.  Tamsin sees the difference because of the
context; `return` is followed by a term, and a production cannot be part of
a term.  (More on terms in a moment.)

    | main = blerp.
    | blerp = return blerp.
    + foo
    + foo
    + foo 0 0 0 0 0
    = blerp

A rule may also consist of the keyword `print` followed by a term, which,
when evaluated, sends the term to the output, and evaluates to the term.
(Mostly this is useful for debugging.  In the following, `world` is
repeated because it is both printed, and the result of the evaluation.)

    | main = print hello & print world.
    + ahoshoshohspohdphs
    = hello
    = world
    = world

A rule may also consist of two subrules joined by the `&` operator.
The `&` operator processes the left-hand side rule.  If the LHS fails, then
the `&` expression fails; otherwise, it continues and processes the
right-hand side rule.  If the RHS fails, the `&` expression fails; otherwise
it evaluates to what the RHS evaluated to.

    | main = "sure" & "begorrah".
    + sure begorrah
    = begorrah

    | main = "sure" & "begorrah".
    + sure milwaukee
    ? expected 'begorrah' found 'milwaukee'

    | main = "sure" & "begorrah".
    + sari begorrah
    ? expected 'sure' found 'sari'

A rule may also consist of two subrules joined by the `|` operator.
The `&` operator processes the left-hand side rule.  If the LHS succeeds,
then the `|` expression evaluates to what the LHS evaluted to, and the
RHS is ignored.  But if the LHS fails, it processes the RHS; if the RHS
fails, the `|` expression fails, but otherwise it evaluates to what the
RHS evaluated to.

For example, this program accepts `0` or `1` but nothing else.

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
to the opposite.  (Note here also that `&` has a higher precedence than `|`.)

    | main = "0" & return 1 | "1" & return 0.
    + 0
    = 1

    | main = "0" & return 1 | "1" & return 0.
    + 1
    = 0

    | main = "0" & return 1 | "1" & return 0.
    + 2
    ? expected '1' found '2'

Evaluation order can be altered by using parentheses, as per usual.

    | main = "0" & ("0" | "1") & "1" & return ok.
    + 0 1 1
    = ok

Note that if the LHS of `|` fails, the RHS is tried at the position of
the stream that the LHS started on.  This property is called "backtracking".

    | ohone = "0" & "1".
    | ohtwo = "0" & "2".
    | main = ohone | ohtwo.
    + 0 2
    = 2

Note that `print` and `return` never fail.  Thus, code like the following
is "useless":

    | main = foo & print hi | return useless.
    | foo = return bar | print useless.
    = hi
    = hi

Note that `return` does not exit the production immediately — although
this behaviour may be re-considered...

    | main = return hello & print not_useless.
    = not_useless
    = not_useless

Alternatives can select code to be executed, based on the input.

    | main = aorb & print aorb | cord & print cord & return ok.
    | aorb = "a" & print ay | "b" & print bee.
    | cord = "c" & print see | eorf & print eorf.
    | eorf = "e" & print ee | f & print eff.
    + e
    = ee
    = eorf
    = cord
    = ok

If there is more input available than what we wrote the program to consume,
the program still succeeds.

    | main = "sure" & "begorrah".
    + sure begorrah tis a fine day
    = begorrah

And that's the basics.  With these tools, you can write simple
recursive-descent parsers.  For example, to consume nested parentheses
containing a zero:

    | main = parens & "." & return ok.
    | parens = "(" & parens & ")" | "0".
    + 0.
    = ok

    | main = parens & "." & return ok.
    | parens = "(" & parens & ")" | "0".
    + (((0))).
    = ok

(the error message on this test case is a little weird; it's because of
the backtracking.  It tries to match `(((0)))` against the beginning of
input, and fails, because the last `)` is not present.  So it tries to
match `0` at the beginning instead, and fails that too.)

    | main = parens & "." & return ok.
    | parens = "(" & parens & ")" | "0".
    + (((0)).
    ? expected '0' found '('

(the error message on this one is much more reasonable...)

    | main = parens & "." & return ok.
    | parens = "(" & parens & ")" | "0".
    + ((0))).
    ? expected '.' found ')'

To consume a comma-seperated list of one or more bits:

    | main = bit & {"," & bit} & ".".
    | bit = "0" | "1".
    + 1.
    = .

    | main = bit & {"," & bit} & ".".
    | bit = "0" | "1".
    + 0,1,1,0,1,1,1,1,0,0,0,0,1.
    = .

(again, backtracking makes the error a little odd)

    | main = bit & {"," & bit} & ".".
    | bit = "0" | "1".
    + 0,,1,0.
    ? expected '.' found ','

    | main = bit & {"," & bit} & ".".
    | bit = "0" | "1".
    + 0,10,0.
    ? expected '.' found ','

### EOF and any ###

The keyword `□` may be used to match against the end of the input
(colloquially called "EOF".)

    | main = "sure" & "begorrah" & □.
    + sure begorrah
    = EOF

This is how you can make it error out if there is extra input remaining.

    | main = "sure" & "begorrah" & □.
    + sure begorrah tis a fine day
    ? expected EOF found 'tis'

The end of the input is a virtual infinite stream of □'s.  You can match
against them until the cows come home.  The cows never come home.

    | main = "sure" & "begorrah" & □ & □ & □.
    + sure begorrah
    = EOF

The symbol `any` matches any token defined by the scanner except □.

    | main = any & any & any.
    + (@)
    = )

    | main = any & any & any.
    + words words words
    = words

    | main = any & any.
    + words
    ? expected any token, found EOF

### Variables ###

When a production is called, the result that it evaluates to may be stored
in a variable.  Variables are local to the production.

    | main = blerp → B & return B.
    | blerp = "blerp".
    + blerp
    = blerp

Names of Variables must be Capitalized.

    | main = blerp → b & return b.
    | blerp = "blerp".
    ? Expected variable

In fact, the result of not just a production, but any rule, may be sent
into a variable by `→`.  Note that `→` has a higher precedence than `&`.

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

This isn't the only way to set a variable.  You can also do so unconditionally
with `set`.

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

### Optional rules and Asterated rules ###

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

### fail and dynamic matching ###

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

As mentioned, `"foo"` matches a literal token `foo` in the buffer.  But
what if you want to match something dynamic, something you have in a
variable?  You can do that with `«»`:

    | main = set E = foo & «E».
    + foo
    = foo

    | main = set E = foo & «E».
    + bar
    ? expected 'foo' found 'bar'

### Arguments to Productions ###

A production may be called with arguments.

    | main = blerf(world).
    | blerf(X) = return hello(X).
    = hello(world)

No variables from the caller leak into the called production.

    | main = set F = whatever & donkey(world).
    | donkey(E) = return hello(F).
    ? KeyError

Note that this makes the «»-form more interesting.

    | main = bracketed(a) & bracketed(b) & return ok.
    | bracketed(X) = «X» & "stuff" & «X».
    + a stuff a b stuff b
    = ok

    | main = bracketed(a) & bracketed(b) & return ok.
    | bracketed(X) = «X» & "stuff" & «X».
    + a stuff a b stuff a
    ? expected 'b' found 'a'

We need to be able to test arguments somehow.  We can do that with
pattern-matching, which works in Tamsin very similarly to how it
works in Erlang (except here, there are no guards or list sugar.)

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

What does this get us?  Functional programming!  Let's parse a tree, then
return the rightmost bottommost leaf.

    | main = tree → T & rightmost(T).
    | tree = "tree" & "(" & tree → L & "," & tree → R & ")" & return tree(L, R)
    |      | "0" | "1" | "2".
    | rightmost(tree(L,R)) = rightmost(R).
    | rightmost(X) = return X.
    + tree(tree(0,1),tree(0,tree(1,2)))
    = 2

### Implicit Buffer ###

Object-oriented languages sometimes have an "implicit self".  That means
when you say just `foo`, it's assumed (at least, to begin with,) to be a
method or field on the current object that is in context.

Tamsin, clearly, has an _implicit buffer_.  This is the buffer on which
scanning/parsing operations like terminals operate.  When you call another
production from a production, that production you call gets the same
implicit buffer you were working on.  And `main` gets standard input as
its implicit buffer.

So, also clearly, there should be some way to alter the implicit buffer
when you call another production.  And there is.

The syntax for this is postfix `@`, because you're pointing the production
"at" some other text...

    | main = set T = tree(a,tree(b,c)) & tree @ T.
    | tree = "tree" & "(" & tree → L & "," & tree → R & ")" & return fwee(L, R)
    |      | "a" | "b" | "c".
    + doesn't matter
    = fwee(a, fwee(b, c))

### Case Study: Parsing and Evaluating S-Expressions ###

We now have enough tools at our disposal to parse and evaluate simple
S-expressions (from Lisp or Scheme).

We can write such a parser with `{}`, but the result is a bit messy.

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

Nice.  But it returns a term that's backwards.  So we need to write a
reverser.  In Erlang, this would be

    reverse([H|T], A) -> reverse(T, [H|A]).
    reverse([], A) -> A.

In Tamsin, it's:

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

But it's not deep.  It only reverses the top-level list.

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

So here's a deep reverser.

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

### Implicit Scanner ###

Not only is there an implicit buffer, there is also, obviously, an implicit
scanner.  By default, this is the scanner for the Tamsin language.  But
you can change it!

#### A prolix note on implementation ####

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

### Changing the scanner ###

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

### Aside #2 ###

[...]

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

### Anyway, back to scanning ###

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

### More tests ###

A literal string may contain escape sequences.  Note, I hate escape sequences!
So I might not leave this feature in, or, at least, not quite like this.

    | main = ("a" & "\"" & "b" & return 'don\'t') using ☆char.
    + a"b
    = don't

    | main = ("a" & "\\" & "b" & return 'don\\t') using ☆char.
    + a\b
    = don\t

    | main = ("a" & "\n" & "b" & return 'don\nt') using ☆char.
    + a
    + b
    = don
    = t

    | main = ("a" & "\t" & "b" & return 'don\tt') using ☆char.
    + a	b
    = don	t

And note, `"foo"` is syntactic sugar for `«「foo」»`.

    | main = "foo" & «「foo」» & «'foo'» & return yup.
    + foo foo foo
    = yup

And note, underscores are allowed in production and variable names,
and atoms without quotes.

    | main = this_prod.
    | this_prod = set Var_name = this_atom & return Var_name.
    = this_atom

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

### And now, back to "parse-patterns" ###

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
then.  Which we will do.  But first,

Variables that are set in a parse-pattern formals are available to
the production's rule.

    | main = donkey(world).
    | donkey[any → E] = return hello(E).
    = hello(world)

No variables from the caller leak into the called production.

    | main = set F = whatever & donkey(world).
    | donkey[any → E] = return hello(F).
    ? KeyError

Terms are stringified before being matched.

    | main = donkey(a(b(c))).
    | donkey["a" & "(" & "b" & "(" & "c" & ")" & ")"] = return yes.
    = yes

Thus, in this sense at least, terms are sugar for strings.

    | main = donkey('a(b(c))').
    | donkey["a" & "(" & "b" & "(" & "c" & ")" & ")"] = return yes.
    = yes

The rule formals may call on other rules in the program.

    | main = donkey('pair(pair(0,1),1)').
    | donkey[pair → T] = return its_a_pair(T).
    | donkey[bit → T] = return its_a_bit(T).
    | thing = pair | bit.
    | pair = "pair" & "(" & thing → A & "," & thing → B & ")" & return pair(A,B).
    | bit = "0" | "1".
    = its_a_pair(pair(pair(0, 1), 1))

Appendix A. Grammar
-------------------

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

Appendix B. Notes
-----------------

These are now out of context, and kept here for historical purposes.

### an aside, written a while back ###

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

### stuff about implicit buffer ###

Here's a "problem": the implicit buffer is a string, and we don't have
strings in the data domain, we have terms.  This "problem" is easily
"solvable": we can stringify the term.  This is a terrible "solution",
but it lets us experiment further.

This would be nicer if we had a syntax to put arbitrary text in an atom.
Hey, how about 「this is an atom」?  Hmmm...

### Implementation Notes ###

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
