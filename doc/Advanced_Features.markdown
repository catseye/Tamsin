Advanced Features of the Tamsin Language
========================================

This document is a **work in progress**.

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
        
### Tests that used to be in README ###

Hello, world!

    | main = 'Hello, world!'.
    = Hello, world!

Make a story more exciting!

    | main = S ← '' & {("." & '!' | "?" & '?!' | any) → C & S ← S + C} & S.
    + Chapter 1
    + ---------
    + It was raining.  She knocked on the door.  She heard
    + footsteps inside.  The door opened.  The butler peered
    + out.  "Hello," she said.  "May I come in?"
    = Chapter 1
    = ---------
    = It was raining!  She knocked on the door!  She heard
    = footsteps inside!  The door opened!  The butler peered
    = out!  "Hello," she said!  "May I come in?!"

Parse an algebraic expression for syntactic correctness.

    | main = (expr0 & eof & 'ok').
    | expr0 = expr1 & {"+" & expr1}.
    | expr1 = term & {"*" & term}.
    | term = "x" | "y" | "z" | "(" & expr0 & ")".
    + x+y*(z+x+y)
    = ok

Parse an algebraic expression to a syntax tree.

    | main = expr0.
    | expr0 = expr1 → E1 & {"+" & expr1 → E2 & E1 ← add(E1,E2)} & E1.
    | expr1 = term → E1 & {"*" & term → E2 & E1 ← mul(E1,E2)} & E1.
    | term = "x" | "y" | "z" | "(" & expr0 → E & ")" & E.
    + x+y*(z+x+y)
    = add(x, mul(y, add(add(z, x), y)))

Translate an algebraic expression to RPN (Reverse Polish Notation).

    | main = expr0 → E & walk(E).
    | expr0 = expr1 → E1 & {"+" & expr1 → E2 & E1 ← add(E1,E2)} & E1.
    | expr1 = term → E1 & {"*" & term → E2 & E1 ← mul(E1,E2)} & E1.
    | term = "x" | "y" | "z" | "(" & expr0 → E & ")" & E.
    | walk(add(L,R)) = walk(L) → LS & walk(R) → RS & return LS+RS+' +'.
    | walk(mul(L,R)) = walk(L) → LS & walk(R) → RS & return LS+RS+' *'.
    | walk(X) = return ' '+X.
    + x+y*(z+x+y)
    =  x y z x + y + * +

Reverse a list.

    | main = reverse(pair(a, pair(b, pair(c, nil))), nil).
    | reverse(pair(H, T), A) = reverse(T, pair(H, A)).
    | reverse(nil, A) = A.
    = pair(c, pair(b, pair(a, nil)))

Parse and evaluate a Boolean expression.

    | main = expr0 → E using scanner & eval(E).
    | expr0 = expr1 → E1 & {"or" & expr1 → E2 & E1 ← or(E1,E2)} & E1.
    | expr1 = term → E1 & {"and" & term → E2 & E1 ← and(E1,E2)} & E1.
    | term = "true" | "false" | "(" & expr0 → E & ")" & E.
    | eval(and(A, B)) = eval(A) → EA & eval(B) → EB & and(EA, EB).
    | eval(or(A, B)) = eval(A) → EA & eval(B) → EB & or(EA, EB).
    | eval(X) = X.
    | and(true, true) = 'true'.
    | and(A, B) = 'false'.
    | or(false, false) = 'false'.
    | or(A, B) = 'true'.
    | scanner = scan using $.char.
    | scan = {" "} & ("(" | ")" | token).
    | token = "f" & "a" & "l" & "s" & "e" & 'false'
    |       | "t" & "r" & "u" & "e" & 'true'
    |       | "o" & "r" & 'or'
    |       | "a" & "n" & "d" & 'and'.
    + (falseortrue)andtrue
    = true

Parse a CSV file and write out the 2nd-last field of each record.  Handles
commas and double-quotes inside quotes.

    | main = line → L & L ← lines(nil, L) &
    |        {"\n" & line → M & L ← lines(L, M)} & extract(L) & ''.
    | line = field → F & {"," & field → G & F ← fields(G, F)} & F.
    | field = strings | bare.
    | strings = string → T & {string → S & T ← T + '"' + S} & T.
    | string = "\"" & T ← '' & {!"\"" & any → S & T ← T + S} & "\"" & T.
    | bare = T ← '' & {!(","|"\n") & any → S & T ← T + S} & T.
    | extract(lines(Lines, Line)) = extract(Lines) & extract_field(Line).
    | extract(L) = L.
    | extract_field(fields(Last, fields(This, X))) = print This.
    | extract_field(X) = return X.
    + Harold,1850,"21 Baxter Street",burgundy
    + Smythe,1833,"31 Little Street, St. James",mauve
    + Jones,1791,"41 ""The Gardens""",crimson
    = 21 Baxter Street
    = 31 Little Street, St. James
    = 41 "The Gardens"
