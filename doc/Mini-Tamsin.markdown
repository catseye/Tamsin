Mini-Tamsin
===========

This is just the first few parts of the spec ("Micro-Tamsin" plus variables
and things) that the Tamsin compiler written in Tamsin can handle.

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
    ? 

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
*   flatten(T) when T is a constructor S(T1,...Tn) results in an atom comprising
    
        S · "(" · flatten(T1) · "," · ... · "," · flatten(Tn) · ")"
    
    where `·` is string concatenation;
*   flatten(EOF) is not defined.

The result of flattening is always an atom.

Ground terms also support an operation called _reprifying_ (also sometimes
called "readable stringification").  It is very similar to flattening, but
results in an atom, the contents of which is always a legal syntactic atom
in term context in a Tamsin program.  (Flattening a term does not always
guarantee this because, for example, flattening `'\n'` results in an actual
newline.)

*   repr(T) when T is an atom whose text consists only of one or more ASCII
    characters in the ranges `a` to `z`, `A` to `Z`, `0` to `9`, and `_`,
    results in T;

*   repr(T) when T is any other atom results in an atom comprising
    
        "'" · T′ · "'"
    
    where T′ is T with all non-printable and non-ASCII bytes replaced by
    their associated `\xXX` escape sequences (for example, newline is `\x0a`),
    and with `\` replaced by `\\` and `'` replaced by `\'`;

*   repr(T) when T is a constructor S(T1,...Tn) whose text S consists only of
    one or more ASCII characters in the ranges listed above, results in

        S · "(" · repr(T1) · "," · ... · "," · repr(Tn) · ")"

*   repr(T) when T is a any other constructor S(T1,...Tn) results in
    
        "'" · S′ · "'" · "(" · repr(T1) · ", " · ... · ", " · repr(Tn) · ")"
    
    where `·` is string concatenation and S′ is defined the same way as T′ is
    for atoms;
    
*   repr(EOF) is `EOF`.

Note that in the above, "printable" means ASCII characters between 32 ` `
(space) and 126 `~`.  It is not dependent on locale.

Also, `\xXX` escapes will always be output in lowercase, e.g. `\x0a`, not
`\x0A`.

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
    ? expected

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
    ? expected

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

    # | main = "a" & "\x4a" & "b" & print 'don\x4at'.
    # + aJb
    # = donJt
    # = donJt

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

(Not so sure about this one.  It makes the grammar compflicated.)

    # | main = S ← blerf & "x" & 'frelb'(S).
    # + x
    # = frelb(blerf)

But it must be quoted, or Tamsin'll think it's a production.

    | main = S ← blerf & "x" & frelb.
    + x
    ? 

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
    ? expected

Not that (for now) `/`'s cannot be nested.  But you can make a sub-production
for this purpose.

    | main = ("*" & string)/nil/cons.
    | string = $:alnum/''.
    + *hi*there*nice*day*isnt*it
    = cons(it, cons(isnt, cons(day, cons(nice, cons(there, cons(hi, nil))))))

### System Module ###

The module `$` contains a number of built-in productions which would not
be possible or practical to implement in Tamsin.  See Appendix C for a list.

In fact, we have been using the `$` module already!  But our usage of it
has been hidden under some syntactic sugar.

    | main = $:expect(k).
    + k
    = k

    | main = $:expect(k).
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

Here's `$:mkterm`, which takes an atom and a list and creates a constructor.

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

Here's `$:equal`, which takes two terms, L and R.  If L and R are equal,
succeeds and returns that term which they both are.  Otherwise fails.

Two atoms are equal if their texts are identical.

    | main = $:equal('hi', 'hi').
    = hi

    | main = $:equal('hi', 'lo').
    ? term 'hi' does not equal 'lo'

Two constructors are equal if their texts are identical, they have the
same number of subterms, and all of their corresponding subterms are equal.

    | main = $:equal(hi(there), hi(there)).
    = hi(there)

    | main = $:equal(hi(there), lo(there)).
    ? term 'hi(there)' does not equal 'lo(there)'

    | main = $:equal(hi(there), hi(here)).
    ? term 'hi(there)' does not equal 'hi(here)'

    | main = $:equal(hi(there), hi(there, there)).
    ? term 'hi(there)' does not equal 'hi(there, there)'

Here's `$:emit`, which takes an atom and outputs it.  Unlike `print`, which
is meant for debugging, `$:emit` does not append a newline, and is 8-bit-clean.

    | main = $:emit('`') & $:emit('wo') & ''.
    = `wo

    -> Tests for functionality "Intepret Tamsin program (pre- & post-processed)"
    
`$:emit` is 8-bit-clean: if the atom contains unprintable characters,
`$:emit` does not try to make them readable by UTF-8 or any other encoding.
(`print` may or may not do this, depending on the implementation.)

    # | main = $:emit('\x00\x01\x02\xfd\xfe\xff') & ''.
    # = 000102fdfeff0a

    -> Tests for functionality "Intepret Tamsin program"

Here's `$:repr`, which takes a term and results in an atom which is the
result of reprifying that term (see section on Terms, above.)

    | main = $:repr(hello).
    = hello

    | main = $:repr('016fo_oZZ').
    = 016fo_oZZ

    | main = $:repr('016fo$oZZ').
    = '016fo$oZZ'

    | main = $:repr('').
    = ''

    | main = $:repr('016\n016').
    = '016\x0a016'

    | main = $:repr(hello(there, world)).
    = hello(there, world)

    | main = V ← '♡' & $:repr('□'(there, V)).
    = '\xe2\x96\xa1'(there, '\xe2\x99\xa1')

    | main = $:repr(a(b(c('qu\'are\\')))).
    = a(b(c('qu\'are\\')))

    # | main = $:repr('\x99').
    # = '\x99'

Here's `$:reverse`, which takes a term E, and a term of the form
`X(a, X(b, ... X(z, E)) ... )`, and returns a term of the form
`X(z, X(y, ... X(a, E)) ... )`.  The constructor tag X is often `cons`
or `pair` or `list` and E is often `nil`.

    | main = $:reverse(list(a, list(b, list(c, nil))), nil).
    = list(c, list(b, list(a, nil)))

E need not be an atom.

    | main = $:reverse(list(a, list(b, list(c, hello(world)))), hello(world)).
    = list(c, list(b, list(a, hello(world))))

If the tail of the list isn't E, an error occurs.

    | main = $:reverse(list(a, list(b, list(c, hello(world)))), nil).
    ? malformed list

If some list constructor doesn't have two children, an error occurs.

    | main = $:reverse(list(a, list(b, list(nil))), nil).
    ? malformed list

The constructor tag can be anything.

    | main = $:reverse(foo(a, foo(b, foo(c, nil))), nil).
    = foo(c, foo(b, foo(a, nil)))

But if there is a different constructor somewhere in the list, well,

    | main = $:reverse(foo(a, fooz(b, foo(c, nil))), nil).
    ? malformed list

You can reverse an empty list.

    | main = $:reverse(nil, nil).
    = nil

But of course,

    | main = $:reverse(nil, zilch).
    ? malformed list

This is a shallow reverse.  Embedded lists are not reversed.

    | main = $:reverse(list(a, list(list(1, list(2, nil)), list(c, nil))), nil).
    = list(c, list(list(1, list(2, nil)), list(a, nil)))

Here's gensym.

    | main = $:gensym('foo').
    = foo1

    | main = $:gensym('foo') → F & $:gensym('foo') → G & $:equal(F, G).
    ? 'foo1' does not equal 'foo2'
