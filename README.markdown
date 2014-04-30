Tamsin
======

Tamsin is a strange little language that can't decide if it's a
language-definition language like CoCo/R or a functional language
like Erlang or a practical extraction and reporting language like...
that one practical extraction and reporting language whose name
escapes me at the moment.

Basically, every time I see someone use a compiler-compiler like `yacc`
or a parser combinator library, part of me thinks, "Well why didn't
you just write a recursive-descent parser?  Recursive-descent parsers
are easy to write and they make for extremely pretty code!"
And what does a recursive-descent parser do?  It consumes input.  But
don't *all* algorithms consume input?  So why not have a language which
makes it easy to write recursive-descent parsers, and force all programs
to be written as recursive-descent parsers?  Then all code will be pretty!
(Yeah, sure, OK.)

Where I'm going with this, I don't quite know yet.  It is a
**work in progress** and will definitely change as time goes on.

Teaser Examples
---------------

In these, the stuff prefixed with `|` is the Tamsin program, `+` is the
input to the program, and `=` is the expected output.

    -> Tests for functionality "Intepret Tamsin program"

Parse an algebraic expression for correctness.

    | main = (expr0 & □ & return ok) using ☆char.
    | expr0 = expr1 & {"+" & expr1}.
    | expr1 = term & {"*" & term}.
    | term = "x" | "y" | "z" | "(" & expr0 & ")".
    + x+y*(z+x+y)
    = ok

    | main = (expr0 & □ & return ok) using ☆char.
    | expr0 = expr1 & {"+" & expr1}.
    | expr1 = term & {"*" & term}.
    | term = "x" | "y" | "z" | "(" & expr0 & ")".
    + x+xy
    ? expected EOF found 'y'

Parse an algebraic expression to a syntax tree.

    | main = expr0 using ☆char.
    | expr0 = expr1 → E1 & {"+" & expr1 → E2 & set E1 = add(E1,E2)} & return E1.
    | expr1 = term → E1 & {"*" & term → E2 & set E1 = mul(E1,E2)} & return E1.
    | term = "x" | "y" | "z" | "(" & expr0 → E & ")" & return E.
    + x+y*(z+x+y)
    = add(x, mul(y, add(add(z, x), y)))

Make a story more exciting!

    | main = collect using ☆char.
    | collect = set S = '' & {translate → C & set S = S + C} & return S.
    | translate = □ & fail done | "." & return '!' | "?" & return '?!' | any.
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

Reverse a list.

    | main = reverse(pair(a, pair(b, pair(c, nil))), nil).
    | reverse(pair(H, T), A) =
    |   reverse(T, pair(H, A)) → TR &
    |   return TR.
    | reverse(nil, A) =
    |   return A.
    = pair(c, pair(b, pair(a, nil)))

Parse and evaluate a Boolean expression.

    | main = expr0 → E using ☆tamsin & eval(E).
    | expr0 = expr1 → E1 & {"or" & expr1 → E2 & set E1 = or(E1,E2)} & return E1.
    | expr1 = term → E1 & {"and" & term → E2 & set E1 = and(E1,E2)} & return E1.
    | term = "true" | "false" | "(" & expr0 → E & ")" & return E.
    | eval(and(A, B)) = eval(A) → EA & eval(B) → EB & and(EA, EB).
    | eval(or(A, B)) = eval(A) → EA & eval(B) → EB & or(EA, EB).
    | eval(true) = return true.
    | eval(false) = return false.
    | and(true, true) = return true.
    | and(A, B) = return false.
    | or(false, false) = return false.
    | or(A, B) = return true.
    + (false or true) and true
    = true

For more information
--------------------

*   [The Tamsin Language Specification](doc/Tamsin.markdown)

TODO
----

*   dictionary values in variables?
*   arbitrary non-printable characters in terms and such
*   special form that consumes rest of input from the Tamsin source
