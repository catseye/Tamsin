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

Tamsin is still a **work in progress**, but the basic ideas have crystallized,
and a 0.1 release will probably happen soon (with the usual caveat that
version 0.2 might look completely different.)

Teaser Examples
---------------

In these, the stuff prefixed with `|` is the Tamsin program, `+` is the
input to the program, and `=` is the expected output.

    -> Tests for functionality "Intepret Tamsin program"

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

    | main = expr0 → E using $.tamsin & eval(E).
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
    + (false or true) and true
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

Parse and evaluate a little S-expression-based language.

*   See [Case Study: Evaluating S-expressions](doc/Case_Study.markdown)

For more information
--------------------

If the above has piqued your curiosity, you may want to read the specification
documents, which contain many more small examples written to demonstrate
(and test) the syntax and behavior of Tamsin:

*   [The Tamsin Core Language Specification](doc/Tamsin.markdown)
*   [Advanced Features of the Tamsin Language](doc/Advanced_Features.markdown)

Quick Start
-----------

This repository contains the reference implementation of Tamsin, written in
Python.  It can interpret a Tamsin program, and compile a program written
in (core) Tamsin to C.  To start using it,

*   Install [toolshelf](https://github.com/catseye/toolshelf).
*   `toolshelf dock gh:catseye/tamsin`

Or just clone this repo and make a symbolic link to `bin/tamsin` somewhere
on your path (or alter your path to contain the `bin/` directory of this repo.)

Then you can run `tamsin` like so:

*   `tamsin run eg/csv_parse.tamsin < eg/names.csv`

You can also compile to C and compile the C to an executable and run the
executable all in one step, from the repo directory, like so:

*   `./loadngo eg/csv_extract.tamsin < eg/names.csv`

While the reference implementation is fine for prototyping, note that initial
benchmarking reveals the compiled C programs to be about 30x faster.  (I'll
write up something more detailed about this eventually.)

Design Goals
------------

*   Allow writing very compact parsers, interpreters, and compilers.
    (Not *quite* to the point of being a golfing language, but nearly.)
*   Allow parsers, interpreters, and compilers to be quickly prototyped.
*   Allow writing (almost) anything using (almost) only recursive-descent
    parsing techniques.
*   Provide means to solve practical problems.
*   Keep the language simple (grammar should fit on a page)
*   Have a relatively simple reference implementation (currently ~1700 lines,
    including everything — debugging and the C runtime used by the compiler.)

License
-------

BSD-style license; see the file [LICENSE](LICENSE).

Related work
------------

*   CoCo/R
*   Parsec
*   Squishy2K, Arboretuum, and Treacle

TODO
----

*   meta-circular implementation of scanner -- what we have is pretty close
*   meta-circular implementation of parser
*   meta-circular implementation of interpreter!
*   system library in its own Python module
*   `bin/tamsin runast astfile.txt` -- for testing the meta-circular parser
*   `bin/tamsin runscan scanfile.txt` -- for testing the meta-circular scanner
*   `bin/tamsin scan file.tamsin` -- to generate a scanfile
*   refactor nastier bits of the compiler
*   8-bit clean strings, in both Python and C.  tests for these as string
    literals, ability to scan them on input, and ability to produce them
    on output.
*   better command-line argument parsing

### document ###

*   pragmas and aliases

### lower-priority/experimental ###

*   use `←` instead of `@`, why not?
*   `¶foo` means production called `foo`, to disambiguate
    (this would mean unaliasing is less necessary -- call your production
    `¶return` if you like) -- ASCII version?  `p^foo`?
*   pattern match in send:
    *   `fields → F@fields(H,T) & H`
*   maps, implemented as hash tables.
    *   `Table ← {} & fields → F@fields(H,T) & Table[H] ← T`
*   global variables.  or better, variables scoped to a set of productions.
*   these idioms are so common there ought to be a form for them:
    *   `set A = '' & {rule → B & A ← A + B} & A`
    *   `set A = nil & {rule → B & A ← cons(A, B)} & A`
    indeed, this is a fold!  something like...
    *   `fold rule '' +`
    *   `fold rule nil cons`
    i.e.
    *   `"fold" & expr0 & term & ("+" | term)`
    that certainly implies that `+` is a constructor though.  hmmm...
    well, we could start with the term version, like:
    
        expr0 = expr1 → E & fold ("+" & expr1) E add.
        expr1 = term → E & fold ("*" & term) E mul.
        term = "x" | "y" | "z" | "(" & expr0 → E & ")" & E.

*   auto-generate terms from productions, like Rooibos does
*   `;` = `&`?
*   pretty-print AST for error messages
*   have analyzer, interpreter, compiler all inherit from ASTWalker or smth?
*   `$.alpha`
*   `$.digit`
*   arbitrary non-printable characters in terms and such
*   don't consume stdin until asked to scan.
*   numeric values... somehow.  number('65') = #65.  decode(ascii, 'A') = #65.
*   token classes... somehow.  (then numeric is just a special token class?)
*   term expressions -- harder than it sounds
*   be generous and allow "xyz" in term context position?
*   non-backtracking versions of `|` and `{}`?  (very advanced)
*   «» could be an alias w/right sym (`,,`, `„`)
    (still need to scan it specially though)
*   special form that consumes rest of input from the Tamsin source -- gimmick
*   feature-testing: `$.exists('$.blargh') | do_without_blargh`
*   ternary: `foo ? bar : baz` -- if foo succeeded, do bar, else do baz.
*   a second implementation, in C -- with compiler to C and meta-circular
    implementation, this can be generated!
