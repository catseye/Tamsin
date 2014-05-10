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
