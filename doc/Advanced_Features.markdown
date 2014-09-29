Advanced Features of the Tamsin Language
========================================

This document is a **work in progress**.

Note that none of these features are in Tamsin version 0.1 (although the
reference implementation might support them or at least the syntax for
them — they should be regarded as undefined in 0.1.  They may appear in
0.2.)

    -> Tests for functionality "Intepret Tamsin program"

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

Advanced Assignment
-------------------

The right-hand side of `→` can actually be more than a variable name;
it can be a pattern term, just like is used in the arguments, above.
This can be useful for "deconstructing" a compound return value from a
production to extract the parts you want.

    | main = foo → pair(A,B) & return A.
    | foo = return pair(wellington, trainer).
    = wellington

    | main = foo → pair(A,B) & return B.
    | foo = return pair(wellington, trainer).
    = trainer

Even without variables, this can also be useful simply to assert something
returns some value.

    | main = foo → b & print 'yes' | print 'no'.
    | foo = return a.
    = no
    = no

    | main = foo → b & print 'yes' | print 'no'.
    | foo = return b.
    = yes
    = yes

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
    | donkey[any → E using word] = return hello(E).
    | word = (T ← '' & {$.alnum → S & T ← T + S} & T) using $.char.
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
    | donkey[pair → T using mini] = return its_a_pair(T).
    | donkey[bit → T using mini] = return its_a_bit(T).
    | thing = pair | bit.
    | pair = "pair" & "(" & thing → A & "," & thing → B & ")" & return pair(A,B).
    | bit = "0" | "1".
    | mini = (bit | "(" | ")" | "," | word) using $.char.
    | word = (T ← '' & {$.alnum → S & T ← T + S} & T).
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
