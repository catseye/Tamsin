Tamsin
======

Tamsin is an oddball little language that can't decide if it's a
[meta-language](doc/Philosophy.markdown#meta-language), a
[programming language](doc/Philosophy.markdown#programming-language), or a
[rubbish lister](doc/Philosophy.markdown#rubbish-lister).

Its primary goal is to allow the rapid development of **parsers**,
**interpreters**, and **compilers**, and to allow them to be expressed
compactly.  Golf your grammar!

Tamsin is still a **work in progress**, but the basic ideas have crystallized,
and a 0.1 release may happen soon (with the usual caveat that version 0.2
might look completely different.)

Code Examples
-------------

Hello, world:

    main = 'Hello, world!'.

Parse an algebraic expression — 4 lines of code.

    main = (expr0 & eof & 'ok').
    expr0 = expr1 & {"+" & expr1}.
    expr1 = term & {"*" & term}.
    term = "x" | "y" | "z" | "(" & expr0 & ")".

Translate an algebraic expression to RPN (Reverse Polish Notation) — 7
lines of code.

    main = expr0 → E & walk(E).
    expr0 = expr1 → E1 & {"+" & expr1 → E2 & E1 ← add(E1,E2)} & E1.
    expr1 = term → E1 & {"*" & term → E2 & E1 ← mul(E1,E2)} & E1.
    term = "x" | "y" | "z" | "(" & expr0 → E & ")" & E.
    walk(add(L,R)) = walk(L) → LS & walk(R) → RS & return LS+RS+' +'.
    walk(mul(L,R)) = walk(L) → LS & walk(R) → RS & return LS+RS+' *'.
    walk(X) = return ' '+X.

Make a story more exciting — 1 line of code.

    main = S ← '' & {("." & '!' | "?" & '?!' | any) → C & S ← S + C} & S.

Parse a CSV file (handling quoted commas and quotes correctly) and write
out the 2nd-last field of each record — 11 lines of code.

    main = line → L & L ← lines(nil, L) &
           {"\n" & line → M & L ← lines(L, M)} & extract(L) & ''.
    line = field → F & {"," & field → G & F ← fields(G, F)} & F.
    field = strings | bare.
    strings = string → T & {string → S & T ← T + '"' + S} & T.
    string = "\"" & T ← '' & {!"\"" & any → S & T ← T + S} & "\"" & T.
    bare = T ← '' & {!(","|"\n") & any → S & T ← T + S} & T.
    extract(lines(Lines, Line)) = extract(Lines) & extract_field(Line).
    extract(L) = L.
    extract_field(fields(Last, fields(This, X))) = print This.
    extract_field(X) = return X.

For more information
--------------------

If the above has piqued your curiosity, you may want to read the specification
documents, which contain many more small examples written to demonstrate
(and test) the syntax and behavior of Tamsin:

*   [The Tamsin Core Language Specification](doc/Tamsin.markdown)
*   [Advanced Features of the Tamsin Language](doc/Advanced_Features.markdown)

Quick Start
-----------

The Tamsin reference repository is [hosted on Github](https://github.com/catseye/tamsin).

This repository contains the reference implementation of Tamsin, called
`tamsin`, written in Python.  It can interpret a Tamsin program, and compile
a program written in (core) Tamsin to C.  The distribution also contains
implementations of the Tamsin scanner and parser written in Tamsin itself
(although we're still a ways from a fully bootrapped implementation.)

While the interpreter is fine for prototyping, note that some informal
benchmarking revealed the compiled C programs to be about 30x faster.

To start using `tamsin`,

*   Clone the repository — `git clone https://github.com/catseye/tamsin`
*   Either:
    *   Put the repo's `bin` directory on your `$PATH`, or
    *   Make a symbolic link to `bin/tamsin` somewhere already on your `$PATH`.
*   Errr... that's it.

(Or, to make those steps trivial, you could use
[toolshelf](https://github.com/catseye/toolshelf) and run
`toolshelf dock gh:catseye/tamsin`)

Then you can run `tamsin` like so:

*   `tamsin run eg/csv_parse.tamsin < eg/names.csv`

You can also compile to C and compile the C to an executable and run the
executable all in one step, like so:

*   `tamsin loadngo eg/csv_extract.tamsin < eg/names.csv`

Design Goals
------------

*   Allow writing very compact parsers, interpreters, and compilers.
    (Not *quite* to the point of being a golfing language, but nearly.)
*   Allow parsers, interpreters, and compilers to be quickly prototyped.
*   Allow writing (almost) anything using (almost) only recursive-descent
    parsing techniques.
*   Provide means to solve practical problems.
*   Keep the language simple (grammar should fit on a page.)
*   Have a relatively simple reference implementation (currently less than
    3 KLoc, including everything — debugging and the C runtime used by the
    compiler.)

License
-------

BSD-style license; see the file [LICENSE](LICENSE).

Related work
------------

*   [CoCo/R](http://www.scifac.ru.ac.za/coco/)
*   [Parsec](http://www.haskell.org/haskellwiki/Parsec)
*   [Squishy2K](http://catseye.tc/node/Squishy2K),
    [Arboretuum](http://catseye.tc/node/Arboretuum), and
    [Treacle](http://catseye.tc/node/Treacle)
