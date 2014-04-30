The Tamsin Language Specification
=================================

This document is a **work in progress**.

This document, plus the reference implementation `tamsin.py`, is as close
to normative as we're going to come for the time being.  But they are still
far from normative.

    -> Tests for functionality "Intepret Tamsin program"

Fundaments
----------

A Tamsin program consists of one or more productions.  A production consists
of a name and a rule.  Among other things, a rule may be a _non-terminal_,
which is the name of a production, or a _terminal_, which is a literal string
in double quotes.  (A full grammar for Tamsin can be found in Appendix A.)

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
    | eorf = "e" & print ee | f & print eff.
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

*   expand(T, C) when T is an atom, results in that atom;
*   expand(T, C) when T is a constructor S(T1,...,Tn) results in a new
    term S(expand(T1, C), ... expand(Tn, C);
*   expand(T, C) when T is a variable results in C[T] (look up T in C
    and evaluate to that.  If T is not present in C, the result is
    not defined.)

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

In these contexts, a bareword evaluates to an atom.

    | main = return hello.
    = hello

But an atom can contain arbitrary text.  To include an atom which contains
spaces or other things which are not "bareword", enclose it in single quotes.

    | main = return Hello, world!
    ? Expected '.' at ', world!'

    | main = return 'Hello, world!'.
    = Hello, world!

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

And note, underscores are allowed in production and variable names,
and atoms without quotes.

    | main = this_prod.
    | this_prod = set Var_name = this_atom & return Var_name.
    = this_atom

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

Modules
-------

This section needs to be written.  Basically, a module is a set of
productions inside a namespace.  In the future you may be able to write
and import modules, but for now, there is one built-in module called `$`
and it is always in scope.

The module `$` contains a number of built-in productions which would not
be possible or practical to implement in Tamsin.  See Appendix B for a list.

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

Terms are flattened for use in `«»`.  So in fact, the `"foo"` syntax is just
syntactic sugar for `«'foo'»`.

    | main = «'f'».
    + f
    = f

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

    | main = "abc" using $.char.
    + abc
    ? expected 'abc' found 'a'

There is also a scanner which implements the lexical rules of the Tamsin
language itself.  Since most (all!) implementations of Tamsin will
implement the Tamsin scanner, it should be no great burden to a Tamsin
implementation to expose it to the Tamsin program.

    | main = ("a" & "b" & "c") using $.tamsin.
    + a b c
    = c

    | main = ("a" & "b" & "c") using $.tamsin.
    + abc
    ? expected 'a' found 'abc'

    | main = "abc" using $.tamsin.
    + abc
    = abc

(TODO: more notes on the handiness of the tamsin scanner here.)

You can mix two scanners in one production.  Note that the tamsin scanner
doesn't consume spaces after a token, and that the char scanner doesn't skip
spaces.

    | main = "dog" using $.tamsin & ("c" & "a" & "t") using $.char & return ok.
    + dog cat
    ? expected 'c' found ' '

But we can tell it to skip spaces...

    | main = "dog" using $.tamsin
    |      & ({" "} & "c" & "a" & "t") using $.char
    |      & return ok.
    + dog        cat
    = ok

Note that the scanner in force is lexically contained in the `using`.  Outside
of the `using`, scanning returns to whatever scanner was in force before the
`using`.

    | main = ("c" & "a" & "t" & " ") using $.char & "dog" using $.tamsin.
    + cat dog
    = dog

On the other hand, variables set with one scanner can be accessed by another
scanner, as long as they're in the same production.

    | main = ("c" & "a" & "t" → G) using $.char
    |      & ("dog" & return G) using $.tamsin.
    + cat dog
    = t

**Note**: you need to be careful when using `using`!  Beware putting
`using` inside a rule that can fail, i.e. the LHS of `|` or inside a `{}`.
Because if it does fail and the interpreter reverts the scanner to its
previous state, its previous state may have been with a different scanning
logic.  The result may well be eurr.

### Writing your own scanner ###

As mentioned, a scanner is just a production which, each time it is called,
returns an atom, which the client will treat as a token.

    | main = scanner using $.char.
    | scanner = {scan → A & print A} & ".".
    | scan = {" "} & ("-" & ">" & return '->' | "(" | ")" | "," | ";" | word).
    | word = letter → L & {letter → M & set L = L + M}.
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

When you name a production in the program with `using`, that production
should return a token each time it is called.  We call this scanner a
"production-defined scanner" or just "production scanner".  In the
following, we use a production scanner based on the `scanner` production.
(But we use the Tamsin scanner to implement it, so it's not that interesting.)

    | main = program using scanner.
    | scanner = scan using $.tamsin.
    | scan = "cat" | "dog".
    | program = "cat" & "dog".
    + cat dog
    = dog

Note that while it's conventional for a production scanner to return terms
similar to the strings it scanned, this is just a convention, and may be
subverted:

    | main = program using scanner.
    | scanner = scan using $.tamsin.
    | scan = "cat" & return meow | "dog" & return woof.
    | program = "meow" & "woof".
    + cat dog
    = woof

We can also implement a production scanner with the ☆char scanner.  This is
more useful.

    | main = program using scanner.
    | scanner = scan using $.char.
    | scan = "a" | "b" | "@".
    | program = "a" & "@" & "b" & return ok.
    + a@b
    = ok

If the production scanner fails to match the input text, it will return an EOF.
This is a little weird, but.  Well.  Watch this space.

    | main = program using scanner.
    | scanner = scan using $.char.
    | scan = "a" | "b" | "@".
    | program = "a" & "@" & "b" & return ok.
    + x
    ? expected 'a' found 'EOF'

On the other hand, if the scanner understands all the tokens, but the parser
doesn't see the tokens it expects, you get the usual error.

    | main = program using scanner.
    | scanner = scan using $.char.
    | scan = "a" | "b" | "@".
    | program = "a" & "@" & "b" & return ok.
    + b@a
    ? expected 'a' found 'b'

We can write a slightly more realistic scanner, too.

    | main = program using scanner.
    | scanner = scan using $.char.
    | scan = "c" & "a" & "t" & return cat
    |      | "d" & "o" & "g" & return dog.
    | program = "cat" & "dog".
    + catdog
    = dog

Parsing using a production scanner ignores any extra text given to it,
just like the built-in parser.

    | main = program using scanner.
    | scanner = scan using $.char.
    | scan = (
    |            "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |        ).
    | program = "cat" & "dog".
    + catdogfoobar
    = dog

Herein lie an excessive number of tests that I wrote while I was debugging.
Some of them will be cleaned up at a future point.

    | main = scan using $.tamsin.
    | scan = "cat" & $.print(1) &
    |        ("cat" & $.print(2) | "dog" & $.print(3)) &
    |        "dog" & $.print(4) & return ok.
    + cat cat dog
    = 1
    = 2
    = 4
    = ok

    | main = scan using $.tamsin.
    | scan = "cat" & $.print(1) &
    |        ("cat" & $.print(2) | "dog" & $.print(3)) &
    |        "dog" & $.print(4) & return ok.
    + cat dog dog
    = 1
    = 3
    = 4
    = ok

    | main = program using scanner.
    | scanner = scan using $.char.
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
    | scanner = scan using $.char.
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

### Advanced use of `using` ###

A production scanner may contain an embedded `using` and use another
production scanner.

    | main = program using scanner1.
    | 
    | scanner1 = scan1 using $.char.
    | scan1 = "a" | "b" | "c" | "(" & other & ")" & return list.
    | 
    | other = xyz using scanner2.
    | xyz = "1" & "1" | "1" & "2" | "2" & "3".
    | 
    | scanner2 = scan2 using $.char.
    | scan2 = "x" & return 1 | "y" & return 2 | "z" & return 3.
    | program = "c" & "list" & "a".
    + c(xx)a
    = a

    | main = program using scanner1.
    | 
    | scanner1 = scan1 using $.char.
    | scan1 = "a" | "b" | "c" | "(" & other & ")" & return list.
    | 
    | other = xyz using scanner2.
    | xyz = "1" & "1" | "1" & "2" | "2" & "3".
    | 
    | scanner2 = scan2 using $.char.
    | scan2 = "x" & return 1 | "y" & return 2 | "z" & return 3.
    | program = "c" & "list" & "a".
    + c(yy)a
    ? expected 'list' found 'EOF'

Maybe an excessive number of minor variations on that...

    | main = program using scanner1.
    | 
    | scanner1 = scan1 using $.char.
    | scan1 = "a" | "b" | "c" | "(" & xyz using scanner2 & ")" & return list.
    | 
    | xyz = "1" & "1" | "1" & "2" | "2" & "3".
    | 
    | scanner2 = scan2 using $.char.
    | scan2 = "x" & return 1 | "y" & return 2 | "z" & return 3.
    | program = "c" & "list" & "a".
    + c(xx)a
    = a

    | main = program using scanner1.
    | 
    | scanner1 = scan1 using $.char.
    | scan1 = "a" | "b" | "c" | "(" & {other} & ")" & return list.
    | 
    | other = xyz using scanner2.
    | xyz = "1" & "1" | "1" & "2" | "2" & "3".
    | 
    | scanner2 = scan2 using $.char.
    | scan2 = "x" & return 1 | "y" & return 2 | "z" & return 3.
    | program = "c" & "list" & "a".
    + c(xxxyyzxy)a
    = a

    | main = program using scanner1.
    | 
    | scanner1 = scan1 using $.char.
    | scan1 = "a" | "b" | "c" | "(" & {xyz using scanner2} & ")" & return list.
    | 
    | xyz = "1" & "1" | "1" & "2" | "2" & "3".
    | 
    | scanner2 = scan2 using $.char.
    | scan2 = "x" & return 1 | "y" & return 2 | "z" & return 3.
    | program = "c" & "list" & "a".
    + c(xxxyyzxy)a
    = a

    | main = program using scanner1.
    | 
    | scanner1 = scan1 using $.char.
    | scan1 = "a" | "b" | "c"
    |       | "(" & {xyz → R using scanner2} & ")" & return R.
    | 
    | xyz = "1" & "1" & return 11 | "1" & "2" & return 12 | "2" & "3" & return 23.
    | 
    | scanner2 = scan2 using $.char.
    | scan2 = "x" & return 1 | "y" & return 2 | "z" & return 3.
    | program = "c" & ("11" | "12" | "23") → R & "a" & return R.
    + c(xxxyyzxy)a
    = 12

The production being applied with the production scanner can also switch
its own scanner.  It switches back to the production scanner when done.

    | main = program using scanner.
    | 
    | scanner = scan using $.char.
    | scan = {" "} & set T = '' & {("a" | "b" | "c") → S & set T = T + S}.
    | 
    | program = "abc" & "cba" & "bac".
    + abc    cba bac
    = bac

    | main = program using scanner.
    | 
    | scanner = scan using $.char.
    | scan = {" "} & set T = '' & {("a" | "b" | "c") → S & set T = T + S}.
    | 
    | program = "abc" & (subprogram using subscanner) & "bac".
    | 
    | subscanner = subscan using $.char.
    | subscan = {" "} & set T = '' & {("s" | "t" | "u") → S & set T = T + S}.
    | 
    | subprogram = "stu" & "uuu".
    + abc    stu   uuu bac
    = bac

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

    | main = set T = 't(a,t(b,c))' & tree @ T.
    | tree = "t" & "(" & tree → L & "," & tree → R & ")" & return fwee(L, R)
    |      | "a" | "b" | "c".
    + doesn't matter
    = fwee(a, fwee(b, c))

Evaluation
----------

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
    | tree = "t" & "r" & "e" & "e" &
    |        "(" & tree → L & "," & tree → R & ")" & return tree(L, R)
    |      | "0" | "1" | "2".
    | rightmost(tree(L,R)) = rightmost(R).
    | rightmost(X) = return X.
    + tree(tree(0,1),tree(0,tree(1,2)))
    = 2

See Case Study here.

### Rule Formals ###

Then we no longer pattern-match terms.  They're just strings.  So we... we
parse them.  Here's a preview, and we'll get more serious about this further
below.

Now that you can create scanners and parsers to your heart's desire, we
return to the reason you would even need to: terms vs. rules in the
"formal arguments" part of a production definition.

    | main = ("a" | "b" | "c") → C & donkey('f' + C) → D & return D.
    | donkey["f" & ("a" | "c")] = return yes.
    | donkey["f" & "b"] = return no.
    + a
    = yes

    | main = ("a" | "b" | "c") → C & donkey('f' + C) → D & return D.
    | donkey["f" & ("a" | "c")] = return yes.
    | donkey["f" & "b"] = return no.
    + b
    = no

    | main = ("a" | "b" | "c") → C & donkey('f' + C) → D & return D.
    | donkey["f" & ("a" | "c")] = return yes.
    | donkey["f" & "b"] = return no.
    + c
    = yes

Variables that are set in a parse-pattern formals are available to
the production's rule.

    | main = donkey(world).
    | donkey[any → E] = return hello(E).
    = hello(w)

    | main = donkey(world).
    | donkey[any → E using $.tamsin] = return hello(E).
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
    | donkey[pair → T using $.tamsin] = return its_a_pair(T).
    | donkey[bit → T using $.tamsin] = return its_a_bit(T).
    | thing = pair | bit.
    | pair = "pair" & "(" & thing → A & "," & thing → B & ")" & return pair(A,B).
    | bit = "0" | "1".
    = its_a_pair(pair(pair(0, 1), 1))

Advanced Programming
--------------------

Pragmas.

    | @alias zrrk 2 = jersey.
    | @unalias zrrk.
    | main = foo.
    | foo = "b".
    + b
    = b

Alias.

    | @alias foo 2 = jersey.
    | main = jersey(a,b) & foo c d.
    | jersey(A,B) = «A» & «B».
    + abcd
    = d

Unalias.

    | @alias foo 2 = jersey.
    | @unalias foo.
    | main = jersey(a,b) & foo c d.
    | jersey(A,B) = «A» & «B».
    + abcd
    ? Expected '.' at ' c d

Can't unalias an alias that isn't established.

    | @alias foo 2 = jersey.
    | @unalias bar.
    | main = return ok.
    ? KeyError

Appendix A. Grammar
-------------------

    Grammar    ::= {"@" Pragma "."} Production {Production "."}.
    Production ::= ProdName ["(" [Term {"," Term} ")" | "[" Expr0 "]"] "=" Expr0.
    Expr0      ::= Expr1 {("||" | "|") Expr1}.
    Expr1      ::= Expr2 {("&&" | "&") Expr2}.
    Expr2      ::= Expr3 ["using" ProdRef].
    Expr3      ::= Expr4 ["→" Variable].
    Expr4      ::= "(" Expr0 ")"
                 | "[" Expr0 "]"
                 | "{" Expr0 "}"
                 | "set" Variable "=" Term
                 | "return" Term
                 | "fail" Term
                 | LitToken
                 | ProdRef ["(" [Term {"," Term} ")"] ["@" Term].
    Term       ::= Term0.
    Term0      ::= Term1 {"+" Term1}.
    Term1      ::= Atom ["(" {Term0} ")"]
                 | Variable.
    ProdRef    ::= [ModuleRef "."] ProdName.
    ModuleRef  ::= "$".
    Pragma     ::= "alias" ProdName Integer "=" ProdRef
                 | "unalias" ProdName.
    Atom       ::= ("'" {any} "'" | { "a".."z" | "0".."9" }) using $.char.
    Variable   ::= ("A".."Z" { "a".."z" | "0".."9" }) using $.char.
    ProdName   ::= { "a".."z" | "0".."9" } using $.char.

Appendix B. System Module
-------------------------

*   `$.char` -- character scanner production
*   `$.tamsin` -- character scanner production
*   `$.eof` -- succeeds on eof and returns eof, otherwise fails
*   `$.any` -- fails on eof, succeeds and returns token on any other token
*   `$.print(X)` -- prints X to output as a side-effect, returns X
*   `$.fail(X)` -- always fails, giving X as the error message
*   `$.return(X)` -- always succeeds, returning X

Appendix C. Notes
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

### aside #2 ###

Well this is all very nice, very pretty I'm sure you'll agree, but it doesn't
hang together too well.  Figuration is easier than composition.  The thing is
that we still have these two domains, the domain of strings that we parse
and the domain of terms that we match.  We need to bring them closer together.
This section is just ideas for that.

One is that instead of, or alongside terms, we compose strings.

First, we put arbitrary text in an atom, with `「this syntax」`.  Then we allow
terms to be concatenated with `•`.  It looks real cool!  But also, it's kind
of annoying.  So we also allow `'this ' + 'syntax.'`.

### ... ###

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

### ... #2 ###

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
