The Tamsin Language Specification, version 0.3-PRE
==================================================

This document is a **work in progress**.

*Note* that this document only specifies the behaviour of Tamsin version
0.3-PRE.  The reference interpreter in fact supports a few more features
than are listed here.  Those features are listed in the
[Advanced Features document](Advanced_Features.markdown), and may appear
in a future version of Tamsin (like 0.4) but they are *not* yet a part of
0.3.

(Note also that -PRE versions are moving targets that may change rapidly,
without the version number changing.)

This document, plus the reference implementation `tamsin`, is as close
to normative as we're going to come for the time being.  But they are still
a ways from being definitive.

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
*   A special, unique symbol called _EOF_ is a term;
*   A _constructor_, written S(T1, T2, ... Tn) where S is a character
    string and T1 through Tn are terms (called the _subterms_ of T), is a term;
*   A _variable_, written as a character string where the first character
    is a capital Latin letter, is a term;
*   Nothing else is a term.

In fact, there is little theoretical difference between an atom and a
constructor with zero subterms, but they are considered different things
for conceptual clarity.

Note that EOF is not at atom.

A term is called _ground_ if it does not contain any variables.

Terms support an operation called _expansion_, which also requires a
context C (a map from variable names to ground terms.)

*   expand(T, C) when T is an atom or EOF evaluates to T;
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
    
    where `·` is string concatenation;
*   flatten(EOF) is not defined.

The result of flattening is always an atom.

The input to a Tamsin production is, in fact, an atom (although it's hardly
atomic; "atom" is sort of a quaint moniker for the role these objects play.)

The contexts in Tamsin which expect a term expression are `return`, `set`, and
arguments to productions (but you haven't seen those yet.)  In these contexts,
a bareword evaluates to an atom (rather than a non-terminal.)

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

    | main = "a" & "\"" & "b" & print 'don\'t'.
    + a"b
    = don't
    = don't

    | main = "a" & "\\" & "b" & print 'don\\t'.
    + a\b
    = don\t
    = don\t

    | main = "a" & "\n" & "b" & print 'don\nt'.
    + a
    + b
    = don
    = t
    = don
    = t

    | main = "a" & "\t" & "b" & print 'don\tt'.
    + a	b
    = don	t
    = don	t

The escape sequence \x must be followed by two hex digits.

    | main = "a" & "\x4a" & "b" & print 'don\x4at'.
    + aJb
    = donJt
    = donJt

Note also that you can print a constructor.

    | main = print hi(there('I\'m'(a(constructor)))).
    = hi(there(I'm(a(constructor))))
    = hi(there(I'm(a(constructor))))

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
    ? no 'main:frelb' production defined

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

Static Checking
---------------

Note that the production named by a non-terminal must exist in the program,
even if it is never evaluated.

    | main = "k" | something_undefined.
    + k
    ? something_undefined

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

### folds ###

The following idiom is essentially a *fold* from functional programming.

    | main = T ← '' & {$:alnum → S & T ← T + S} & return T.
    + dogwood
    = dogwood

It is so common, that Tamsin supports a special form for it.  The infix
operator `/` takes a rule on the left-hand side, and a term (used as the
initial value) on the right-hand side, and expands to the above.

    | main = $:alnum/''.
    + dogwood
    = dogwood

    | main = $:alnum/'prefix'.
    + dogwood.
    = prefixdogwood

You can use any rule you desire, not just a non-terminal, on the LHS of `/`.

    | main = ("0" | "1")/'%'.
    + 0110110110.
    = %0110110110

Note that the RHS of `/` is a term expression, so it can contain a `+`.

    | main = ("0" | "1")/'%' + '&'.
    + 0110110110.
    = %&0110110110

If there is an additional `/`, it must be followed by an atom.  This atom
will be used as a constructor, instead of the concat operation.

    | main = $:alnum/nil/cons.
    + dog.
    = cons(g, cons(o, cons(d, nil)))

Note that the middle of `//` is a term expression.

    | main = $:alnum/cat+food/cons.
    + dog.
    = cons(g, cons(o, cons(d, catfood)))

Note that the RHS of `//` is *not* a term expression.

    | main = $:alnum/ni+l/co+ns.
    + dog.
    ? Expected '.' at '+ns.'

Not that (for now) `/`'s cannot be nested.  But you can make a sub-production
for this purpose.

    | main = ("*" & string)/nil/cons.
    | string = $:alnum/''.
    + *hi*there*nice*day*isnt*it
    = cons(it, cons(isnt, cons(day, cons(nice, cons(there, cons(hi, nil))))))

Modules
-------

This section needs to be written.  Basically, a module is a set of
productions inside a namespace.  There is one built-in module called `$`
and it is always in scope.

### System Module ###

The module `$` contains a number of built-in productions which would not
be possible or practical to implement in Tamsin.  See Appendix C for a list.

In fact, we have been using the `$` module already!  But our usage of it
has been hidden under some syntactic sugar.

    | main = $:expect(k).     # same as "k"
    + k
    = k

    | main = $:expect(k).     # same as "k"
    + l
    ? expected 'k' found 'l'

The section about aliases needs to be written too.

Here's `$:alnum`, which only consumes tokens where the first character is
alphanumeric.

    | main = "(" & {$:alnum → A} & ")" & A.
    + (abc123deefghi459876jklmnopqRSTUVXYZ0)
    = 0

    | main = "(" & {$:alnum → A} & ")" & A.
    + (abc123deefghi459876!jklmnopqRSTUVXYZ0)
    ? expected ')' found '!'

Here's `$:upper`, which only consumes tokens where the first character is
uppercase alphabetic.

    | main = "(" & {$:upper → A} & ")" & A.
    + (ABCDEFGHIJKLMNOPQRSTUVWXYZ)
    = Z

    | main = "(" & {$:upper → A} & ")" & A.
    + (ABCDEFGHIJKLMNoPQRSTUVWXYZ)
    ? expected ')' found 'o'

Here's `$:startswith`, which only consumes tokens which start with
the given term.  (For a single-character scanner this isn't very
impressive.)

    | main = "(" & {$:startswith('A') → A} & ")" & A.
    + (AAAA)
    = A

    | main = "(" & {$:startswith('A') → A} & ")" & A.
    + (AAAABAAA)
    ? expected ')' found 'B'

Here's `$:mkterm`, which takes an atom and a list and creates a term.

    | main = $:mkterm(atom, list(a, list(b, list(c, nil)))).
    = atom(a, b, c)

Here's `$:unquote`, which takes three terms, X, L and R, where L and R
must be one-character atoms.  If X begins with L and ends with R then
the contents in-between will be returned as an atom.  Otherwise fails.

    | main = $:unquote('"hello"', '"', '"').
    = hello

    | main = $:unquote('(hello)', '(', ')').
    = hello

    | main = $:unquote('(hello)', '(', '"').
    ? term '(hello)' is not quoted with '(' and '"'

Here's `$:equal`, which takes two terms, L and R, where L and R must be atoms.
If L and R are the same atom (the strings are identical), succeeds and returns
that atom.  Otherwise fails.

    | main = $:equal('hi', 'hi').
    = hi

    | main = $:equal('hi', 'lo').
    ? term 'hi' does not equal 'lo'

Here's `$:emit`, which takes an atom and outputs it.  Unlike `print`, which
is meant for debugging, `$:emit` does not append a newline, and is 8-bit-clean.

    | main = $:emit('`') & $:emit('wo') & ''.
    = `wo

    -> Tests for functionality "Intepret Tamsin program (pre- & post-processed)"
    
`$:emit` is 8-bit-clean: if the atom contains unprintable characters,
`$:emit` does not try to make them readable by UTF-8 or any other encoding.
(`print` may or may not do this, depending on the implementation.)

    | main = $:emit('\x00\x01\x02\xfd\xfe\xff') & ''.
    = 000102fdfeff0a

    -> Tests for functionality "Intepret Tamsin program"

### Back to Modules in General ###

`:foo` always means production `foo` in the current module.

    | main = :blah.
    | blah = "b" & print 'hello'.
    + b
    = hello
    = hello

So, you can name your own productions the same as built-in keywords, as
long as you call them with `:foo`.

    | main = :set.
    | set = :return.
    | return = :fail.
    | fail = :print.
    | print = :any.
    | any = :eof.
    | eof = "x".
    + x
    = x

### Defining a Module ###

Here is the syntax for defining a module:

    | blah {
    |   expr = "y".
    | }
    | main = expr.
    | expr = "x".
    + x
    = x

    | blah {
    |   expr = "y".
    | }
    | main = blah:expr.
    | expr = "x".
    + y
    = y

    | blah {
    |   expr = blah:goo.
    |   goo = "y".
    | }
    | main = blah:expr & blah:goo & "@".
    | expr = "x".
    + yy@
    = @

`:foo` (and indeed `foo`) refers to the production `foo` in the
same module as the production where it's called from.

    | blah {
    |   expr = :goo.
    |   goo = "y".
    | }
    | main = blah:expr.
    | goo = "x".
    + y
    = y
    
    | foo {
    |   expr = goo.
    |   goo = "6".
    | }
    | bar {
    |   expr = goo.
    |   goo = "4".
    | }
    | main = foo:goo & bar:goo.
    + 64
    = 4

Can't call a production or a module that doesn't exist.

    | foo {
    |   expr = goo.
    |   goo = "6".
    | }
    | main = foo:zoo.
    ? no 'foo:zoo' production defined
    
    | foo {
    |   expr = goo.
    |   goo = "6".
    | }
    | main = zoo.
    ? no 'main:zoo' production defined
    
    | foo {
    |   expr = goo.
    |   goo = "6".
    | }
    | main = boo:zoo.
    ? no 'boo' module defined

You can have a Tamsin program that is all modules and no productions, but
you can't run it.

    | foo {
    |   main = "6".
    | }
    ? no 'main:main' production defined

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

Note that `+` is part of a "term expression", but cannot be used as a
pattern.

    | main = what(hel+lo).
    | what(he+llo) = 'yes'.
    ? Expected ')'

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

You can select a different scanner for a rule with `using`.  There are
two built-in scanners in the built-in `$` module that you can use:
`$:utf8`, which consumes Unicode characters encoded in UTF-8 (and which
is the default scanner for a Tamsin program), and `$:byte`, which
consumes raw bytes.

    | main = ("a" & "b" & "c") using $:utf8.
    + abc
    = c

    | main = "abc" using $:utf8.
    + abc
    ? expected 'abc' found 'a'

    | main = ("«" | "♡")/''.
    + «♡««♡←
    = «♡««♡

    | main = {"«" | "♡"} & eof.
    + «♡«→«♡
    ? expected EOF found '→'

Here we test the `$:byte` scanner...

    | main = ("a" & "b" & "c") using $:byte.
    + abc
    = c

    | main = "abc" using $:byte.
    + abc
    ? expected 'abc' found 'a'

    -> Tests for functionality "Intepret Tamsin program (pre- & post-processed)"
    
The byte scanner is 8-bit clean.  (The `0a` added to the output is the newline.)

    | main = (any & any & any) using $:byte.
    + 010003
    = 030a

This includes bytes that would be special in UTF-8.

    | main = (any & any → R & any & R) using $:byte.
    + 00ff00
    = ff0a
    
    | main = "\x00" → N using $:byte & return '\x01' + N + '\xff'.
    + 00
    = 0100ff0a

    | main = ("\x07" & ("\xf0" | "\xfa")/'' → N & "\x07") using $:byte & N.
    + 07f0fafaf0f007
    = f0fafaf0f00a

    -> Tests for functionality "Intepret Tamsin program"

You can also define your own scanner by defining a production designed
to return tokens.  Each time it is called, it should return an atom, which
the user of your scanner will see as a scanned token.

When you name a production in the program with `using`, that production
should return a token each time it is called.  We call this scanner a
"production-defined scanner" or just "production scanner".  In the
following, we use a production scanner based on the `scanner` production.

We'll use the following scanner in the next few examples.  It accepts
only the tokens `cat` and `dog`, and no other symbols.
Note that we are not `using` it yet in this example; this example just
demonstrates that the `token` production returns tokens.

    | main = {token → A & print A} & 'ok'.
    | token = ("c" & "a" & "t" & 'cat' | "d" & "o" & "g" & 'dog') using $:utf8.
    + catdogdogcatcatdog
    = cat
    = dog
    = dog
    = cat
    = cat
    = dog
    = ok

Here's a slightly more practical scanner that we'll also use in the next
few examples.

    | main = {token → A & print A} & 'ok'.
    | token = ({" "} & ("(" | ")" | word)) using $:utf8.
    | word = $:alnum → L & {$:alnum → M & set L = L + M} & L.
    + cabbage( bag     gaffe fad ) ()) bag(bagbag bag)
    = cabbage
    = (
    = bag
    = gaffe
    = fad
    = )
    = (
    = )
    = )
    = bag
    = (
    = bagbag
    = bag
    = )
    = ok

There is one guideline to follow: your production which implements a scanner
should itself say what scanner it is `using`.  For example, the `token` scanner
above is implemented using the character scanner.  If this is missing, the
scanner will try to use *itself* as a scanner, with hilarious and generally
unproductive results.

Here is how you would use the above scanner, as a scanner, in a program:

    | main = ("(" & "cons" & ")" & 'ok') using token.
    | 
    | token = ({" "} & ("(" | ")" | word)) using $:utf8.
    | word = $:alnum → L & {$:alnum → M & set L = L + M} & L.
    + ( cons )
    = ok

    | main = ("(" & "cons" & ")" & 'ok') using token.
    | 
    | token = ({" "} & ("(" | ")" | word)) using $:utf8.
    | word = $:alnum → L & {$:alnum → M & set L = L + M} & L.
    + ( quote )
    ? expected 'cons' found 'quote'

Note that while it's conventional for a production scanner to return terms
similar to the strings it scanned, this is just a convention, and may be
subverted:

    | main = ("meow" & "woof") using token.
    | token = ("c" & "a" & "t" & 'meow' | "d" & "o" & "g" & 'woof') using $:utf8.
    + catdog
    = woof

If a production scanner fails to match the input text, it will return an EOF.
The justification for this is that it's the end of the input, as far as
the scanner can understand it.

    | main = program using scanner.
    | scanner = scan using $:utf8.
    | scan = "a" | "b" | "@".
    | program = "a" & "@" & "b" & return ok.
    + x
    ? expected 'a' found 'EOF'

If you don't like that, you can write your scanner to fail the way you want.

    | main = program using scanner.
    | scanner = scan using $:utf8.
    | scan = "a" | "b" | "@" | return bleah.
    | program = "a" & "@" & "b" & return ok.
    + x
    ? expected 'a' found 'bleah'

On the other hand, if the scanner understands all the tokens, but the parser
doesn't see the tokens it expects, you get the usual error.

    | main = program using scanner.
    | scanner = scan using $:utf8.
    | scan = "a" | "b" | "@".
    | program = "a" & "@" & "b" & return ok.
    + b@a
    ? expected 'a' found 'b'

Parsing using a production scanner ignores any extra text given to it,
just like the built-in parser.

    | main = program using scanner.
    | scanner = scan using $:utf8.
    | scan = (
    |            "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |        ).
    | program = "cat" & "dog".
    + catdogfoobar
    = dog

The production scanner properly handles backtracking on a per-token basis.

    | main = program using scanner.
    | scanner = scan using $:utf8.
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
    | scanner = scan using $:utf8.
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

You can mix two scanners in one production.

    | main = "dog" using token & ("!" & "!" & "!") using $:utf8 & return ok.
    | 
    | token = ({" "} & ("(" | ")" | word)) using $:utf8.
    | word = $:alnum → L & {$:alnum → M & set L = L + M} & L.
    + dog!!!
    = ok

Note that the `token` scanner we've defined doesn't consume spaces after a
token, and that the char scanner doesn't skip spaces.

    | main = "dog" using token & ("c" & "a" & "t") using $:utf8 & return ok.
    | 
    | token = ({" "} & ("(" | ")" | word)) using $:utf8.
    | word = $:alnum → L & {$:alnum → M & set L = L + M} & L.
    + dog cat
    ? expected 'c' found ' '

But we can convince it to skip those spaces...

    | main = "dog" using token
    |      & ({" "} & "c" & "a" & "t") using $:utf8
    |      & return ok.
    | 
    | token = ({" "} & ("(" | ")" | word)) using $:utf8.
    | word = $:alnum → L & {$:alnum → M & set L = L + M} & L.
    + dog        cat
    = ok

Note that the scanner in force is lexically contained in the `using`.  Outside
of the `using`, scanning returns to whatever scanner was in force before the
`using`.

    | main = "dog" using token
    |      & ({"."} & "c" & "a" & "t")
    |      & return ok.
    | 
    | token = ({" "} & ("(" | ")" | word)) using $:utf8.
    | word = $:alnum → L & {$:alnum → M & set L = L + M} & L.
    + dog...........cat
    = ok

On the other hand, variables set when one scanner is in effect can be accessed
by rules with another scanner in effect, as long as they're in the same
production.

    | main = ("c" & "a" & "t" → G) using $:utf8
    |      & ("dog" & return G) using token.
    | 
    | token = ({" "} & ("(" | ")" | word)) using $:utf8.
    | word = $:alnum → L & {$:alnum → M & set L = L + M} & L.
    + cat dog
    = t

**Note**: you need to be careful when using `using`!  Beware putting
`using` inside a rule that can fail, i.e. the LHS of `|` or inside a `{}`.
Because if it does fail and the interpreter reverts the scanner to its
previous state, its previous state may have been with a different scanning
logic.  The result may well be eurr.

### Advanced use of `using` ###

A production scanner may contain an embedded `using` and use another
production scanner.

    | main = program using scanner1.
    | 
    | scanner1 = scan1 using $:utf8.
    | scan1 = "a" | "b" | "c" | "(" & other & ")" & return list.
    | 
    | other = xyz using scanner2.
    | xyz = "1" & "1" | "1" & "2" | "2" & "3".
    | 
    | scanner2 = scan2 using $:utf8.
    | scan2 = "x" & return 1 | "y" & return 2 | "z" & return 3.
    | program = "c" & "list" & "a".
    + c(xx)a
    = a

    | main = program using scanner1.
    | 
    | scanner1 = scan1 using $:utf8.
    | scan1 = "a" | "b" | "c" | "(" & other & ")" & return list.
    | 
    | other = xyz using scanner2.
    | xyz = "1" & "1" | "1" & "2" | "2" & "3".
    | 
    | scanner2 = scan2 using $:utf8.
    | scan2 = "x" & return 1 | "y" & return 2 | "z" & return 3.
    | program = "c" & "list" & "a".
    + c(yy)a
    ? expected 'list' found 'EOF'

Maybe an excessive number of minor variations on that...

    | main = program using scanner1.
    | 
    | scanner1 = scan1 using $:utf8.
    | scan1 = "a" | "b" | "c" | "(" & xyz using scanner2 & ")" & return list.
    | 
    | xyz = "1" & "1" | "1" & "2" | "2" & "3".
    | 
    | scanner2 = scan2 using $:utf8.
    | scan2 = "x" & return 1 | "y" & return 2 | "z" & return 3.
    | program = "c" & "list" & "a".
    + c(xx)a
    = a

    | main = program using scanner1.
    | 
    | scanner1 = scan1 using $:utf8.
    | scan1 = "a" | "b" | "c" | "(" & {other} & ")" & return list.
    | 
    | other = xyz using scanner2.
    | xyz = "1" & "1" | "1" & "2" | "2" & "3".
    | 
    | scanner2 = scan2 using $:utf8.
    | scan2 = "x" & return 1 | "y" & return 2 | "z" & return 3.
    | program = "c" & "list" & "a".
    + c(xxxyyzxy)a
    = a

    | main = program using scanner1.
    | 
    | scanner1 = scan1 using $:utf8.
    | scan1 = "a" | "b" | "c" | "(" & {xyz using scanner2} & ")" & return list.
    | 
    | xyz = "1" & "1" | "1" & "2" | "2" & "3".
    | 
    | scanner2 = scan2 using $:utf8.
    | scan2 = "x" & return 1 | "y" & return 2 | "z" & return 3.
    | program = "c" & "list" & "a".
    + c(xxxyyzxy)a
    = a

    | main = program using scanner1.
    | 
    | scanner1 = scan1 using $:utf8.
    | scan1 = "a" | "b" | "c"
    |       | "(" & {xyz → R using scanner2} & ")" & return R.
    | 
    | xyz = "1" & "1" & return 11 | "1" & "2" & return 12 | "2" & "3" & return 23.
    | 
    | scanner2 = scan2 using $:utf8.
    | scan2 = "x" & return 1 | "y" & return 2 | "z" & return 3.
    | program = "c" & ("11" | "12" | "23") → R & "a" & return R.
    + c(xxxyyzxy)a
    = 12

The production being applied with the production scanner can also switch
its own scanner.  It switches back to the production scanner when done.

    | main = program using scanner.
    | 
    | scanner = scan using $:utf8.
    | scan = {" "} & set T = '' & {("a" | "b" | "c") → S & set T = T + S}.
    | 
    | program = "abc" & "cba" & "bac".
    + abc    cba bac
    = bac

    | main = program using scanner.
    | 
    | scanner = scan using $:utf8.
    | scan = {" "} & set T = '' & {("a" | "b" | "c") → S & set T = T + S}.
    | 
    | program = "abc" & (subprogram using subscanner) & "bac".
    | 
    | subscanner = subscan using $:utf8.
    | subscan = {" "} & set T = '' & {("s" | "t" | "u") → S & set T = T + S}.
    | 
    | subprogram = "stu" & "uuu".
    + abc    stu   uuu bac
    = bac

Appendix A. Grammar
-------------------

Here we give an approximation of Tamsin's grammar, in EBNF.  Note however
that this is non-normative; the canonical grammar definition for Tamsin is
written in Tamsin and can be found in `eg/tamsin-parser.tamsin`.

    Grammar    ::= {"@" Pragma "."} Production {Production "."}.
    Production ::= ProdName ["(" [Term {"," Term} ")" | "[" Expr0 "]"] "=" Expr0.
    Expr0      ::= Expr1 {("||" | "|") Expr1}.
    Expr1      ::= Expr2 {("&&" | "&") Expr2}.
    Expr2      ::= Expr3 ["using" ProdRef].
    Expr3      ::= Expr4 [("→" | "->") Variable].
    Expr4      ::= Expr5 ["/" Texpr ["/" Term)]].
    Expr4      ::= "(" Expr0 ")"
                 | "[" Expr0 "]"
                 | "{" Expr0 "}"
                 | "!" Expr0
                 | "set" Variable "=" Texpr
                 | "return" Texpr
                 | "fail" Texpr
                 | Terminal
                 | Variable [("←" | "<-") Texpr]
                 | ProdRef ["(" [Texpr {"," Texpr}] ")"] ["@" Texpr].
    Texpr      ::= Term {"+" Term}.
    Term       ::= Atom ["(" [Term {"," Term}] ")"]
                 | Variable.
    Terminal   ::= DoubleQuotedStringLiteral
                 | ("«" | "<<") Texpr ("»" | ">>").
    ProdRef    ::= [[ModuleRef] ":"] ProdName.
    ModuleRef  ::= "$" | ModName.
    Pragma     ::= "alias" ProdName Integer "=" ProdRef
                 | "unalias" ProdName.
    Atom       ::= ("'" {any} "'" | { "a".."z" | "0".."9" }) using $.char.
    Variable   ::= ("A".."Z" { "a".."z" | "0".."9" }) using $.char.
    ProdName   ::= { "a".."z" | "0".."9" } using $.char.

Appendix B. Tamsin Scanner
--------------------------

This section is non-normative.  The canonical definition of Tamsin's scanner
is written in Tamsin and can be found in `eg/tamsin-scanner.tamsin`.

The Tamsin scanner is designed to be relatively simple and predictable.
One property in particular is that the token returned by this scanner is
identical to the token that is scanned.  (For example, `&` and `&&`
represent the same operator; thus the Tamsin scanner could return `&`
for both of them, or even something more abstract like `OP_SEQUENCE`.
But it doesn't; it returns `&&` for `&&` and `&` for `&`.

        | main = ("&&" → S & "&" → T & 'pair'(S,T)) using $.tamsin.
        + &&&
        = pair(&&, &)

The original design of Tamsin had it expose the Tamsin scanner (for use
with `using`) as `$.tamsin`.  However, this may not be desirable for all
implementations (e.g the compiler-to-C), and the Tamsin scanner has since
been implemented in Tamsin itself (see `eg/tamsin-scanner.tamsin`.)
Therefore `$.tamsin` no longer exists.

Appendix C. System Module
-------------------------

*   `$:alnum` — succeeds only on token which begins with alphanumeric
*   `$:any` — fails on eof, succeeds and returns token on any other token
*   `$:byte` — 8-bit-clean byte scanner production
*   `$:eof` — succeeds on eof and returns eof, otherwise fails
*   `$:equal(L,R)` — succeeds if L and R are the same atom, otherwise fails
*   `$:expect(X)` — succeeds if token is X and returns it, otherwise fails
*   `$:fail(X)` — always fails, giving X as the error message
*   `$:mkterm(A,L)` — given an atom and a list, return a single constructor
*   `$:not(X)` — succeeds only if token is not X or EOF, and returns token
*   `$:return(X)` — always succeeds, returning X
*   `$:print(X)` — prints X to output as a side-effect, returns X
*   `$:startswith(X)` — consumes token if it starts with first character of X
*   `$:unquote(X,L,R)` — consumes nothing; returns X without quotes if X is quoted
*   `$:utf8` — UTF-8-encoded Unicode character scanner production
