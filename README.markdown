Tamsin
======

**Tamsin** is a strange little language that can't decide if it's a
language-definition language like [CoCo/R](http://www.scifac.ru.ac.za/coco/)
or a functional language like [Erlang](http://erlang.org/) or a practical
extraction and reporting language like... that one practical extraction and
reporting language whose name escapes me at the moment.

Basically, every time I see someone use a compiler-compiler like `yacc`
or a parser combinator library, part of me thinks, "Well why didn't
you just write a recursive-descent parser?  Recursive-descent parsers
are easy to write and they make for extremely pretty code!"
And what does a recursive-descent parser do?  It consumes input.  But
don't *all* algorithms consume input?  So why not have a language which
makes it easy to write recursive-descent parsers, and force all programs
to be written as recursive-descent parsers?  Then *all* code will be pretty!
(Yeah, sure, OK.)

Where I'm going with this, I don't quite know yet.  It is a
**work in progress** and will definitely change as time goes on.

Teaser Examples
---------------

In these, the stuff prefixed with `|` is the Tamsin program, `+` is the
input to the program, and `=` is the expected output.

    -> Tests for functionality "Intepret Tamsin program"

Parse an algebraic expression for correctness.

    | main = (expr0 & eof & 'ok').
    | expr0 = expr1 & {"+" & expr1}.
    | expr1 = term & {"*" & term}.
    | term = "x" | "y" | "z" | "(" & expr0 & ")".
    + x+y*(z+x+y)
    = ok

    | main = (expr0 & eof & 'ok').
    | expr0 = expr1 & {"+" & expr1}.
    | expr1 = term & {"*" & term}.
    | term = "x" | "y" | "z" | "(" & expr0 & ")".
    + x+xy
    ? expected EOF found 'y'

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

Make a story more exciting!

    | main = set S = '' & {translate → C & S ← S + C} & S.
    | translate = "." & '!' | "?" & '?!' | any.
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
    | reverse(pair(H, T), A) = reverse(T, pair(H, A)).
    | reverse(nil, A) = A.
    = pair(c, pair(b, pair(a, nil)))

Parse and evaluate a Boolean expression.

    | main = expr0 → E using $.tamsin & eval(E).
    | expr0 = expr1 → E1 & {"or" & expr1 → E2 & E1 ← or(E1,E2)} & E1.
    | expr1 = term → E1 & {"and" & term → E2 & E1 ← and(E1,E2)} & E1.
    | term = "true" | "false" | "(" & expr0 → E & ")" & E.
    | eval(and(A, B)) = eval(A) → EA & eval(B) → EB & and(EA, EB).
    | eval(or(A, B)) = eval(A) → EA & eval(B) → EB & or(EA, EB).
    | eval(true) = 'true'.
    | eval(false) = 'false'.
    | and(true, true) = 'true'.
    | and(A, B) = 'false'.
    | or(false, false) = 'false'.
    | or(A, B) = 'true'.
    + (false or true) and true
    = true

Parse and evaluate a little S-expression-based language.

*   See [Case Study: Evaluating S-expressions](doc/Case_Study.markdown)

For more information
--------------------

If the above has piqued your curiosity, you may want to read the specification,
which contains many more small examples written to demonstrate (and test) the
syntax and behavior of Tamsin:

*   [The Tamsin Language Specification](doc/Tamsin.markdown)

Quick Start
-----------

*   Install [toolshelf](https://github.com/catseye/toolshelf).
*   `toolshelf dock gh:catseye/tamsin`

Or just clone this repo and make a symbolic link to `bin/tamsin` somewhere
on your path (or alter your path to contain the `bin/` directory of this repo.)

Design Goals
------------

*   Allow writing very compact parsers, interpreters, and compilers.
    (Not *quite* to the point of being a golfing language, but nearly.)
*   Allow parsers, interpreters, and compilers to be quickly prototyped.
*   Allow writing (almost) anything using (almost) only recursive-descent
    parsing techniques.
*   Provide means to solve practical problems.
*   Keep the language simple (grammar should fit on a page)
*   Have a relatively simple reference implementation (currently ~900 lines
    of Python, not counting debugging).

License
-------

BSD-style license; see the file [LICENSE](LICENSE).

TODO
----

*   `$.alpha`
*   `$.digit`
*   arbitrary non-printable characters in terms and such
*   don't consume stdin until asked to scan.
*   numeric values... somehow.  number('65') = #65.  decode(ascii, 'A') = #65.
*   token classes... somehow.  (then numeric is just a special token class?)
*   term expressions -- harder than it sounds

### document ###

*   tamsin scanner sanity
*   implied `set` -- maybe get rid of `set` entirely
*   implied `return` of variables and single-quoted constructors
*   $.not
*   pragmas and aliases

### experimental ###

*   be generous and allow "xyz" in term context position?
*   non-backtracking versions of `|` and `{}`?  (very advanced)
*   «» could be an alias w/right sym (`,,`, `„`)
    (still need to scan it specially though)
*   dictionary values in variables?
*   special form that consumes rest of input from the Tamsin source
*   meta-circular implementation of scanner -- what we have is pretty close
*   meta-circular implementation of parser

### performance ###

*   a second implementation, in C
*   a compiler (in Python) *to* C
