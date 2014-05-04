The Tamsin Language Specification
=================================

This document is a **work in progress**.

*Note* that this document only specifies the behaviour of the core language
(which you could also call "Tamsin Level 0" or "Mini-Tamsin" if you like.)
The advanced features, which are also part of the full Tamsin language, are
documented in the [Advanced Features document](Advanced_Features.markdown)
in this directory.

These documents, plus the reference implementation `tamsin.py`, is as close
to normative as we're going to come for the time being.  But they are still
far from definitive.

    -> Tests for functionality "Intepret Tamsin program"

Fundaments
----------

A Tamsin program consists of one or more _productions_.  A production consists
of a name and a _parsing rule_ (or just "rule" for short).  Among other things,
a rule may be a _non-terminal_, which is the name of a production, or a
_terminal_, which is a literal string in double quotes.  (A full grammar for
Tamsin can be found in Appendix A.)

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

Productions can be written that don't look at the input.  A rule may also
consist of the keyword `return`, followed a _term_; this expression simply
evaluates to that term and returns it.  (More on terms later; for now,
think of them as strings.)

So, the following program always outputs `blerp`, no matter what the input is.

    | main = return blerp.
    + fadda wadda badda kadda nadda sadda hey
    = blerp

Note that in the following, `blerp` refers to the production named "blerp"
in one place, and in the other place, it refers to the term `blerp`.  Tamsin
sees the difference because of the context; `return` must be followed by a
term, while a parsing rule cannot be part of a term.

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

    | main = "a" & "p".
    + ap
    = p

    | main = "a" & "p".
    + ak
    ? expected 'p' found 'k'

    | main = "a" & "p".
    + ep
    ? expected 'a' found 'e'

If you are too used to C or Javascript or the shell, you may use `&&`
instead of `&`.

    | main = "a" && "p".
    + ap
    = p

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

If you are too used to C or Javascript or the shell, you may use `||`
instead of `|`.

    | main = "0" || "1".
    + 1
    = 1

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
    + 011
    = ok

Note that if the LHS of `|` fails, the RHS is tried at the position of
the stream that the LHS started on.  This property is called "backtracking".

    | ohone = "0" & "1".
    | ohtwo = "0" & "2".
    | main = ohone | ohtwo.
    + 02
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
    | eorf = "e" & print ee | "f" & print eff.
    + e
    = ee
    = eorf
    = cord
    = ok

Note that the production named by a non-terminal must exist in the program,
even if it is never evaluated.

    | main = "k" | something_undefined.
    + k
    ? something_undefined

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
    ? expected '.' found '0'

Comments
--------

A Tamsin comment is introduced with `#` and continues until the end of the
line.

    | # welcome to my Tamsin program!
    | main = # comments may appear anywhere in the syntax
    |        # and a comment may be followed by a comment
    |   "z".
    + z
    = z

Variables
---------

When a production is called, the result that it evaluates to may be stored
in a variable.  Variables are local to the production.

    | main = blerp → B & blerp & "." & return B.
    | blerp = "a" | "b".
    + ab.
    = a

Note that you don't have to use the Unicode arrow.  You can use an ASCII
digraph instead.

    | main = blerp -> B & blerp & "." & return B.
    | blerp = "a" | "b".
    + ab.
    = a

Names of Variables must be Capitalized.

    | main = blerp → b & return b.
    | blerp = "b".
    ? Expected variable

In fact, the result of not just a production, but any rule, may be sent
into a variable by `→`.  Note that `→` has a higher precedence than `&`.

    | main = ("0" | "1") → B & return B.
    + 0
    = 0

A `→` expression evaluates to the result placed in the variable.

    | main = ("0" | "1") → B.
    + 0
    = 0

This isn't the only way to set a variable.  You can also do so unconditionally
with `set`.

    | main = eee.
    | eee = set E = whatever && set F = stuff && return E.
    + ignored
    = whatever

And note that variables are subject to backtracking, too; if a variable is
set while parsing something that failed, it is no longer set in the `|`
alternative.

    | main = set E = original &
    |          (set E = changed && "0" && "1" | "0" && "2") &
    |        return E.
    + 01
    = changed

    | main = set E = original &
    |          (set E = changed && "0" && "1" | "0" && "2") &
    |        return E.
    + 02
    = original

Terms
-----

We must now digress for a definition of Tamsin's basic data type, the
_term_.

A term T is defined inductively as follows:

*   An _atom_, written as a character string, is a term;
*   A _constructor_, written S(T1, T2, ... Tn) where S is a character
    string and T1 through Tn are terms (called the _subterms_ of T), is a term;
*   A _variable_, written as a character string where the first character
    is a capital Latin letter, is a term;
*   Nothing else is a term.

In fact, an atom is just a constructor with zero subterms.  When written,
the parentheses are left out.

A term is called _ground_ if it does not contain any variables.

Terms support an operation called _expansion_, which also requires a
context C (a map from variable names to ground terms.)

*   expand(T, C) when T is an atom evaluates to the atom T;
*   expand(T, C) when T is a constructor S(T1,...,Tn) evaluates to a new
    term S(expand(T1, C), ... expand(Tn, C));
*   expand(T, C) when T is a variable looks up T in C and, if there is
    a ground term T' associated with T in C, evaluates to T'; otherwise
    the result is not defined.

The result of expansion will always be a ground term.

Ground terms support an operation called _flattening_ (also sometimes called
stringification).

*   flatten(T) when T is an atom, results in that atom;
*   flatten(T) when T is a constructor results in
    
        S · "(" · flatten(T1) · "," · ... · "," · flatten(Tn) · ")"
    
    where `·` is string concatenation.

The result of flattening is always an atom.

The input to a Tamsin production is, in fact, an atom (although it's hardly
atomic.)

The contexts in Tamsin which expect a term expression are `return`, and
`set`.  (and arguments to productions, but you haven't seen those yet.)
In these contexts, a bareword evaluates to an atom (rather than a non-terminal.)

    | main = return hello.
    = hello

But an atom can contain arbitrary text.  To write an atom which contains
spaces or other things which are not "bareword", enclose it in single quotes.

    | main = return Hello, world!
    ? Expected '.' at ', world!'

    | main = return 'Hello, world!'.
    = Hello, world!

Note that the atom `'X'` is not the same as the variable `X`.  Nor is the
atom `'tree(a,b)'` the same as the constructor `tree(a,b)`.

In a term context, a constuctor may be given with parentheses after the
string.

    | main = return hello(world).
    = hello(world)

The bareword rule applies in subterms.

    | main = return hello(beautiful world).
    ? Expected ')' at ' world).'

    | main = return hello('beautiful world').
    = hello(beautiful world)

In a term context, variables may be given.  The term is always expanded
during evaluation.

    | main = set E = world & return hello(E).
    = hello(world)

A term expression may also contain a `+` operator, which evaluates and
flattens both its arguments and concatenates the resulting atoms.

    | main = set E = world & return 'hello, ' + E + '!'.
    = hello, world!

And note, underscores are allowed in production and variable names,
and atoms without quotes.

    | main = this_prod.
    | this_prod = set Var_name = this_atom & return Var_name.
    = this_atom

### Escape Sequences ###

A literal string may contain escape sequences.  Note, I hate escape sequences!
So I might not leave this feature in, or, at least, not quite like this.

    | main = "a" & "\"" & "b" & return 'don\'t'.
    + a"b
    = don't

    | main = "a" & "\\" & "b" & return 'don\\t'.
    + a\b
    = don\t

    | main = "a" & "\n" & "b" & return 'don\nt'.
    + a
    + b
    = don
    = t

    | main = "a" & "\t" & "b" & return 'don\tt'.
    + a	b
    = don	t

### Examples using Terms ###

This program accepts a pair of bits and evaluates to a term, a constructor
`pair`, with the two bits as subterms.

    | main = bit → A & bit → B & return pair(A, B).
    | bit = "0" | "1".
    + 10
    = pair(1, 0)

    | main = bit → A & bit → B & return pair(A, B).
    | bit = "0" | "1".
    + 01
    = pair(0, 1)

This program expects an infinite number of 0's.  It will be disappointed.

    | main = zeroes.
    | zeroes = "0" & zeroes.
    + 00000
    ? expected '0' found 'EOF'

This program expects a finite number of 0's, and returns a term representing
how many it found.  It will not be disappointed.

    | main = zeroes.
    | zeroes = ("0" & zeroes → E & return zero(E)) | return nil.
    + 0000
    = zero(zero(zero(zero(nil))))

We can also use concatenation to construct the resulting term as an atom.

    | main = zeroes.
    | zeroes = ("0" & zeroes → E & return E + 'Z') | return ''.
    + 0000
    = ZZZZ

Implicit `set` and `return`
---------------------------

Unquoted atoms and constructors ("barewords") can have the same names as
productions.  If they are used in rule context, they are assumed to refer
to productions.  If they are used in term context, they are assumed to
refer to terms.

    | main = blerf.
    | blerf = return blerf.
    = blerf

Because variable names cannot be mistaken for productions, if they are used
in rule context and followed by `←`, this is equivalent to `set`.

    | main = S ← blerf & "x" & return S.
    + x
    = blerf

There is of course an ASCII digraph for the left-pointing arrow.  (The
right-pointing symbol in the input in this test is just to get keep my
text editor's syntax highlighting under control.)

    | main = S <- blerf & "x" & return S.
    + x->
    = blerf

If the variable name is not followed by `←`, this is an implied `return`
of the variable's value.

    | main = S ← blerf & "x" & S.
    + x
    = blerf

If a *quoted* term (atom or constructor) is used in rule context, this too
cannot be mistaken for a production.  So this, too, implies a `return` of
that term.

    | main = S ← blerf & "x" & 'frelb'.
    + x
    = frelb

    | main = S ← blerf & "x" & 'frelb'(S).
    + x
    = frelb(blerf)

But it must be quoted, or Tamsin'll think it's a production.

    | main = S ← blerf & "x" & frelb.
    + x
    ? no 'frelb' production defined

### Aside: ← vs. → ###

One may well ask why Tamsin has both `→`, to send the result of a rule
into a variable, and `←`, to send a term into a variable, when both of these
could be done with one symbol, in one direction, and in fact most languages
do it this way (with a symbol like `=`, usually.)

Two reasons:

This way gives us two disjoint syntax contexts (rule context and term
context) which lets us re-use the same symbols (such as lowercased barewords)
for dual purposes.  Which in turn lets us write more compact code.

And also, parsing is a linear process.  When we consume tokens from the
input, whether directly with a terminal, or indirectly via a non-terminal,
we want them to be easily located.  We want all our ducks to be in a row,
so to speak.  This setup ensures that the focus of parsing is always on
the left and not nested inside a term.  Like so:
    
    | main = "(" &
    |        expr → S &
    |        "," &
    |        expr → T &
    |        U ← pair(S,T) &
    |        ")" &
    |        U.
    | expr = "a"
    |      | "b"
    |      | "c".
    + (b,c)
    = pair(b, c)

That said, it is possible to use only the → if you like, by using `return`
(or implicit return!) instead of `set`.  Like so:

    | main = "(" &
    |        expr → S &
    |        "," &
    |        expr → T &
    |        return pair(S,T) → U &
    |        ")" &
    |        U.
    | expr = "a"
    |      | "b"
    |      | "c".
    + (b,c)
    = pair(b, c)

    | main = "(" &
    |        expr → S &
    |        "," &
    |        expr → T &
    |        'pair'(S,T) → U &
    |        ")" &
    |        U.
    | expr = "a"
    |      | "b"
    |      | "c".
    + (b,c)
    = pair(b, c)

In my opinion, this style is not as clear, because at the rule which updates
`U`, `U` itself is the focus and should be on the left.

What about the other way around?  We could introduce some symbol (say, `/`)
which allows a rule in what would otherwise be a term context, for example

    main = "(" &
           S ← /expr &
           "," &
           T ← /expr &
           U ← pair(S,T) &
           ")" &
           U.
    expr = "a"
         | "b"
         | "c".

This would also work, and is more similar to conventional programming
languages; however, in my opinion, it is not as clear either, because in
the rules which parse the sub-expressions, it is `expr` that is the focus
of the logic, rather than the variables the results are being sent into.

Advanced Parsing
----------------

### eof ###

If there is more input available than what we wrote the program to consume,
the program still succeeds.

    | main = "a" & "p".
    + apparently
    = p

The built-in production `eof` may be used to match against the end of the
input (colloquially called "EOF".)

    | main = "a" & "p" & eof.
    + ap
    = EOF

This is how you can make it error out if there is extra input remaining.

    | main = "a" & "p" & eof.
    + apt
    ? expected EOF found 't'

The end of the input is a virtual infinite stream of EOF's.  You can match
against them until the cows come home.  The cows never come home.

    | main = "a" & "p" & eof & eof & eof.
    + ap
    = EOF

### any ###

The built-in production `any` matches any token defined by the scanner
except for EOF.  (Remember that for now "token defined by the scanner"
means "character", but that that can be changed, as you'll see below.)

    | main = any & any & any.
    + (@)
    = )

    | main = any & any.
    + a
    ? expected any token, found EOF

### Optional rules ###

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
    + 0000
    = zero(zero(zero(zero(nil))))

### Iterated rules ###

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
    + 000002
    = 2

So we can rewrite the "zeroes" example to be even... I hesistate to use
the word "simpler", but we can... write it differently.

    | main = zeroes.
    | zeroes = set Z = nil & {"0" && set Z = zero(Z)} & return Z.
    + 0000
    = zero(zero(zero(zero(nil))))

### fail ###

The built-in production `fail` always fails.  This lets you establish
global flags, of a sort.  It takes a term, which it uses as the failure message.

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

### ! ###

The `!` ("not") keyword is followed by a rule.  If the rule succeeds, the `!`
expression fails.  If the rule fails, the `!` expression succeeds.  In
*neither* case is input consumed — anything the rule matched, is backtracked.
Thus `!` should almost always be followed by `&` and something which consumes
input, such as `any`.

    | main = !"k" & any.
    + l
    = l

    | main = !"k" & any.
    + k
    ? expected anything except

    | main = !("k" | "r") & any.
    + l
    = l

    | main = !("k" | "r") & any.
    + k
    ? expected anything except

    | main = !("k" | "r") & any.
    + r
    ? expected anything except

This is particularly useful for parsing strings and comments and anything
that contains arbitrary text terminated by a sentinel.

    | main = "'" & T ← '' & {!"'" & any → S & T ← T + S} & "'" & return T.
    + 'any bloody
    +   gobbledegook *!^*(^@)(@* (*@#(*^*(^(!^
    + you like.'
    = any bloody
    =   gobbledegook *!^*(^@)(@* (*@#(*^*(^(!^
    = you like.

### Dynamic Terminals ###

As mentioned, the terminal `"foo"` matches a literal token `foo` in the buffer.
But what if you want to match something dynamic, something you have in a
variable?  You can do that with `«»`:

    | main = set E = f & «E».
    + f
    = f

    | main = set E = f & «E».
    + b
    ? expected 'f' found 'b'

Note that you don't have to use the Latin-1 guillemets.  You can use the ASCII
digraphs instead.

    | main = set E = f & <<E>>.
    + b
    ? expected 'f' found 'b'

Terms are flattened for use in `«»`.  So in fact, the `"foo"` syntax is just
syntactic sugar for `«'foo'»`.

    | main = «'f'».
    + f
    = f

Oh, and since we were speaking of sentinels earlier...

    | main = {sentineled → A & print A & {" "}} & return ok.
    | sentineled =
    |    "(" &
    |    any → S &
    |    T ← '' & {!«S» & any → A & T ← T + A} & «S» &
    |    ")" &
    |    T.
    + (!do let's ))) put &c. in this string!)   (&and!this!one&)
    = do let's ))) put &c. in this string
    = and!this!one
    = ok

Modules
-------

This section needs to be written.  Basically, a module is a set of
productions inside a namespace.  In the future you may be able to write
and import modules, but for now, there is one built-in module called `$`
and it is always in scope.

The module `$` contains a number of built-in productions which would not
be possible or practical to implement in Tamsin.  See Appendix C for a list.

In fact, we have been using the `$` module already!  But our usage of it
has been hidden under syntactic sugar (which you'll learn more about in
the "Aliases" section below.)

    | main = $.expect(k).     # same as "k"
    + k
    = k

    | main = $.expect(k).     # same as "k"
    + l
    ? expected 'k' found 'l'

The section about aliases needs to be written too.

Here's `$.alnum`, which only consumes alphanumeric tokens.

    | main = "(" & {$.alnum → A} & ")" & A.
    + (abc123deefghi459876jklmnopqRSTUVXYZ0)
    = 0

    | main = "(" & {$.alnum → A} & ")" & A.
    + (abc123deefghi459876!jklmnopqRSTUVXYZ0)
    ? expected ')' found '!'

Here's `$.upper`, which only consumes uppercase alphabetic tokens.

    | main = "(" & {$.upper → A} & ")" & A.
    + (ABCDEFGHIJKLMNOPQRSTUVWXYZ)
    = Z

    | main = "(" & {$.upper → A} & ")" & A.
    + (ABCDEFGHIJKLMNoPQRSTUVWXYZ)
    ? expected ')' found 'o'

Here's `$.startswith`, which only consumes tokens which start with
the given term.  (For a single-character scanner this isn't very
impressive.)

    | main = "(" & {$.startswith('A') → A} & ")" & A.
    + (AAAA)
    = A

    | main = "(" & {$.startswith('A') → A} & ")" & A.
    + (AAAABAAA)
    ? expected ')' found 'B'

Here's `$.mkterm`, which takes an atom and a list and creates a term.

    | main = $.mkterm(atom, list(a, list(b, list(c, nil)))).
    = atom(a, b, c)

Here's `$.unquote`, which takes a term which begins and ends with a
quote symbol (TODO: should be the given quote symbol) and returns
the contents.

    | main = $.unquote('"hello"').
    = hello

Evaluation
----------

### Arguments to Productions ###

A production may be called with arguments.

    | main = blerf(world).
    | blerf(X) = return hello(X).
    = hello(world)

No variables from the caller leak into the called production.

    | main = set FizzBuzzWhatever = whatever & donkey(world).
    | donkey(E) = return hello(FizzBuzzWhatever).
    ? FizzBuzzWhatever

Note that this makes the «»-form more interesting.

    | main = bracketed(a) & bracketed(b) & return ok.
    | bracketed(X) = «X» & "S" & «X».
    + aSabSb
    = ok

    | main = bracketed(a) & bracketed(b) & return ok.
    | bracketed(X) = «X» & "S" & «X».
    + aSabSa
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
    ? No 'blerf' production matched arguments

Thus, we can write productions that recursively call themselves, and
terminate on the base case.

    | main = blerf(tree(tree(tree(a,b),c),d)).
    | blerf(tree(L,R)) = blerf(L).
    | blerf(Other) = return Other.
    = a

What does this get us?  Functional programming!  Let's parse a tree, then
return the rightmost bottommost leaf.

    | main = tree → T & rightmost(T).
    | tree = "t" & "r" & "e" & "e" &
    |        "(" & tree → L & "," & tree → R & ")" & return tree(L, R)
    |      | "0" | "1" | "2".
    | rightmost(tree(L,R)) = rightmost(R).
    | rightmost(X) = return X.
    + tree(tree(0,1),tree(0,tree(1,2)))
    = 2

Advanced Scanning
-----------------

### Changing the scanner in use ###

There is an implicit scanner in effect at any given point in the program.
As you have seen, the default scanner returns single characters.

    | main = "a" & "b" & "c".
    + abc
    = c

    | main = "abc".
    + abc
    ? expected 'abc' found 'a'

You can select a different scanner for a rule with `using`.  A scanner
is just a production designed to return tokens.  There are a number of
different built-in scanners in the built-in `$` module.  The default
character scanner is available as `$.char`.

    | main = ("a" & "b" & "c") using $.char.
    + abc
    = c

TODO: should be a rewritten copy of Advanced Scanning from Advanced
Features document.

    | main = ("cat" & "dog") using word.
    | word = wwww using $.char.
    | wwww = "c" & "a" & "t" & return 'cat'
    |      | "d" & "o" & "g" & return 'dog'.
    + catdog
    = dog

Three good ways to shoot yourself in the foot
---------------------------------------------
    
1, forget that Tamsin is still basically a *programming* language, or at
best an LL(n) grammar, and try to write a left-recursive rule:
    
    expr = expr & "+" & expr | expr & "*" & expr | "0" | "1".

2, base a `{}` loop around something that always succeeds, like `return` or
`eof` at the end of the input.

    expr = {"k" | return l}.
    
3, base a loop around something that doesn't consume any input, like `!`.

    expr = !"\n" & expr

Appendix A. Grammar
-------------------

First, in EBNF:

    Grammar    ::= {"@" Pragma "."} Production {Production "."}.
    Production ::= ProdName ["(" [Term {"," Term} ")" | "[" Expr0 "]"] "=" Expr0.
    Expr0      ::= Expr1 {("||" | "|") Expr1}.
    Expr1      ::= Expr2 {("&&" | "&") Expr2}.
    Expr2      ::= Expr3 ["using" ProdRef].
    Expr3      ::= Expr4 [("→" | "->") Variable].
    Expr4      ::= "(" Expr0 ")"
                 | "[" Expr0 "]"
                 | "{" Expr0 "}"
                 | "!" Expr0
                 | "set" Variable "=" Term
                 | "return" Term
                 | "fail" Term
                 | LitToken
                 | ProdRef ["(" [Term {"," Term}] ")"] ["@" Term].
    Term       ::= Term0.
    Term0      ::= Term1 {"+" Term1}.
    Term1      ::= Atom ["(" [Term {"," Term}] ")"]
                 | Variable.
    ProdRef    ::= [ModuleRef "."] ProdName.
    ModuleRef  ::= "$".
    Pragma     ::= "alias" ProdName Integer "=" ProdRef
                 | "unalias" ProdName.
    Atom       ::= ("'" {any} "'" | { "a".."z" | "0".."9" }) using $.char.
    Variable   ::= ("A".."Z" { "a".."z" | "0".."9" }) using $.char.
    ProdName   ::= { "a".."z" | "0".."9" } using $.char.


Next, in Tamsin.  Approximate.

    grammar    = {"@" & pragma & "."} & production & {production & "."} & eof.
    production = word & ["(" & term & {"," & term} & ")"
                        | "[" & expr0 & "]"] & "=" & expr0.
    expr0      = expr1 & {("|" | "||") & expr1}.
    expr1      = expr2 & {("&" | "&&") & expr2}.
    expr2      = expr3 & ["using" & prodref].
    expr3      = expr4 & [("→" | "->") & variable].
    expr4      = "(" & expr0 & ")"
               | "[" & expr0 & "]"
               | "{" & expr0 & "}"
               | "!" & expr0
               | "set" & variable & "=" & term
               | "return" & term
               | "fail" & term
               | terminal
               | prodref & ["(" & [term & {"," & term}] & ")"] & ["@" & term].
    term       = term0.
    term0      = term1 & {"+" & term1}.
    term1      = atom & ["(" & [term & {"," & term}] & ")"]
               | variable.
    atom       = word | str('\'').
    terminal   = str('"')
               | ("«" | "<<") & term & ("»" | ">>").
    prodref    = [modref & "."] & word.
    modref     = "$".
    pragma     = "alias" & word & word & "=" & prodref
               | "unalias" & word.


Appendix B. Tamsin Scanner
--------------------------

Written in Tamsin.  Should be very close to true.

    tamsin = skippable & (symbol | str('\'') | str('"') | word).
    symbol = "&" & "&" & '&&'
           | "|" & "|" & '||'
           | "-" & ">" & '->'
           | "<" & "-" & '<-'
           | "<" & "<" & '<<'
           | ">" & ">" & '>>'
           | "=" | "(" | ")" | "[" | "]" | "{" | "}" | "!" | "|" | "&"
           | "," | "." | "@" | "+" | "$" | "→" | "←" | "«" | "»".
    str(Q) = «Q» → T & {(escape | !«Q» & any) → S & T ← T + S} & «Q» &
             return T + Q.
    escape = "\\" & "n" & '\n'
           | "\\" & "r" & '\r'
           | "\\" & "t" & '\t'
           | "\\" & "\\" & '\\'
           | "\\" & "'" & '\''
           | "\\" & "\"" & '"'.
    word = $.alnum → T & { ($.alnum | "_") → S & T ← T + S } & T.
    variable = $.upper → T & { ($.alnum | "_") → S & T ← T + S } & T.
    skippable = {whitespace | comment}.
    whitespace = " " | "\t" | "\r" | "\n".
    comment = "#" & {!"\n" & any} & "\n".


Appendix C. System Module
-------------------------

*   `$.alnum` -- succeeds only on token which begins with alphanumeric
*   `$.any` -- fails on eof, succeeds and returns token on any other token
*   `$.char` -- character scanner production
*   `$.eof` -- succeeds on eof and returns eof, otherwise fails
*   `$.expect(X)` -- succeeds if token is X and returns it, otherwise fails
*   `$.fail(X)` -- always fails, giving X as the error message
*   `$.not(X)` -- succeeds only if token is not X or EOF, and returns token
*   `$.return(X)` -- always succeeds, returning X
*   `$.print(X)` -- prints X to output as a side-effect, returns X
*   `$.tamsin` -- Tamsin language scanner production
