Advanced Features of the Tamsin Language
========================================

This document is a **work in progress**.

    -> Tests for functionality "Intepret Tamsin program"

Advanced Programming
--------------------

Before the first production in a program, any number of _pragmas_ may be
given.  Pragmas may affect how the program following them is parsed.
Each pragma begins with a `@` followed by a bareword indicating the
kind of pragma, followed by a number of arguments specific to that kind
of pragma, followed by a `.`.

    | @alias zrrk 2 = jersey.
    | @unalias zrrk.
    | main = foo.
    | foo = "b".
    + b
    = b

### `@alias` ###

The pragma `@alias` introduces an alias.  Its syntax consists of the
name of the alias (a bareword), followed by an integer which indicates
the _arity_, followed by `=`, followed by the contents of the alias
(i.e., what is being aliased; presently, this must be a non-terminal.)

This sets up a syntax rule, in the rule context, that, when the alias
name is encountered, parses as a call to the aliased non-terminal; in
addition, this syntax rule is special in that it looks for exactly
_arity_ number of terms following the alias name.  Parentheses are not
required to delimit these terms.

    | @alias foo 2 = jersey.
    | main = jersey(a,b) & foo c d.
    | jersey(A,B) = «A» & «B».
    + abcd
    = d

The pragma `@unalias` removes a previously-introduced alias.

    | @alias foo 2 = jersey.
    | @unalias foo.
    | main = jersey(a,b) & foo c d.
    | jersey(A,B) = «A» & «B».
    + abcd
    ? Expected '.' at ' c d

It is an error to attempt to unalias an alias that hasn't been established.

    | @alias foo 2 = jersey.
    | @unalias bar.
    | main = return ok.
    ? KeyError

Note that various of Tamin's "keywords" are actually built-in aliases for
productions in the `$` module, and they may be unaliased.

    | @unalias return.
    | main = return ok.
    ? Expected '.' at ' ok.'

    | @unalias return.
    | main = $.return(ok).
    = ok

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
language itself, which are documented in Appendix B.

    | main = ("a" & "b" & "c") using $.tamsin.
    + a b c
    = c

    | main = ("a" & "b" & "c") using $.tamsin.
    + abc
    ? expected 'a' found 'abc'

    | main = "abc" using $.tamsin.
    + abc
    = abc

The Tamsin scanner is designed to be relatively simple and predictable.
One property in particular is that the token returned by this scanner is
identical to the token that is scanned.  (For example, `&` and `&&`
represent the same operator; thus the Tamsin scanner could return `&`
for both of them, or even something more abstract like `OP_SEQUENCE`.
But it doesn't; it returns `&&` for `&&` and `&` for `&`.

    | main = ("&&" → S & "&" → T & 'pair'(S,T)) using $.tamsin.
    + &&&
    = pair(&&, &)

An implementation of Tamsin may or may not expose the Tamsin scanner as
`$.tamsin`; since a Tamsin interpreter will itself implement the Tamsin
scanner, it should be no great burden to expose it to the running program.
However, for a compiler, this may be a different matter.  (However however,
the Tamsin scanner should be simple enough to implement without major
difficulties.  In fact, there is a partial implementation in Tamsin; which
means that `$.tamsin` need not be a system production, but could be 
provided as a library.)

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

We can also implement a production scanner with the char scanner.  This is
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
    | scan = "cat" & print 1 &
    |        ("cat" & print 2 | "dog" & print 3) &
    |        "dog" & print 4 & return ok.
    + cat cat dog
    = 1
    = 2
    = 4
    = ok

    | main = scan using $.tamsin.
    | scan = "cat" & print 1 &
    |        ("cat" & print 2 | "dog" & print 3) &
    |        "dog" & print 4 & return ok.
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

### Auto-term creation from productions ###

An experimental feature.  But Rooibos does it, and it could help make
parser development faster/shorter.  Note that feature is not fully implemented.
Therefore test disabled.

        | main = expr0.
        | expr0! = expr1 & {"+" & expr1}.
        | expr1! = term & {"*" & term}.
        | term = "x" | "y" | "z" | "(" & expr0 & ")".
        + x+y*(z+x+y)
        = expr0(expr1, +, expr1)
        
    