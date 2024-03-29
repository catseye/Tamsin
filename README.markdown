Tamsin
======

Tamsin is an oddball little language that can't decide if it's a
[meta-language](doc/Philosophy.markdown#meta-language), a
[programming language](doc/Philosophy.markdown#programming-language), or a
[rubbish lister](doc/Philosophy.markdown#rubbish-lister).

Its primary goal is to allow the rapid development of **parsers**,
**static analyzers**, **interpreters**, and **compilers**, and to allow them
to be expressed *compactly*.  Golf your grammar!  (Or write it like a decent
human being, if you must.)

The current released version of Tamsin is 0.5-2017.0502.
As indicated by the 0.x version number, it is a **work in progress**,
with the usual caveat that things may change rapidly (and that version 0.6 might
look completely different.)  See [HISTORY](HISTORY.markdown)
for a list of major changes.

Code Examples
-------------

Make a story more exciting in **1 line of code**:

    main = ("." & '!' | "?" & '?!' | any)/''.

Parse an algebraic expression for syntactic correctness in **4 lines of code**:

    main = (expr0 & eof & 'ok').
    expr0 = expr1 & {"+" & expr1}.
    expr1 = term & {"*" & term}.
    term = "x" | "y" | "z" | "(" & expr0 & ")".

Translate an algebraic expression to RPN (Reverse Polish Notation) in
**7 lines of code**:

    main = expr0 → E & walk(E).
    expr0 = expr1 → E1 & {"+" & expr1 → E2 & E1 ← add(E1,E2)} & E1.
    expr1 = term → E1 & {"*" & term → E2 & E1 ← mul(E1,E2)} & E1.
    term = "x" | "y" | "z" | "(" & expr0 → E & ")" & E.
    walk(add(L,R)) = walk(L) → LS & walk(R) → RS & return LS+RS+' +'.
    walk(mul(L,R)) = walk(L) → LS & walk(R) → RS & return LS+RS+' *'.
    walk(X) = return ' '+X.

Parse a CSV file (handling quoted commas and quotes correctly) and write
out the 2nd-last field of each record — in **11 lines of code**:

    main = line → L & L ← lines(nil, L) &
           {"\n" & line → M & L ← lines(L, M)} & extract(L) & ''.
    line = field → F & {"," & field → G & F ← fields(G, F)} & F.
    field = strings | bare.
    strings = string → T & {string → S & T ← T + '"' + S} & T.
    string = "\"" & (!"\"" & any)/'' → T & "\"" & T.
    bare = (!(","|"\n") & any)/''.
    extract(lines(Ls, L)) = extract(Ls) & extract_field(L).
    extract(L) = L.
    extract_field(fields(L, fields(T, X))) = print T.
    extract_field(X) = X.

Evaluate an (admittedly trivial) S-expression based language in
**15 lines of code**:

    main = sexp → S using scanner & reverse(S, nil) → SR & eval(SR).
    scanner = ({" "} & ("(" | ")" | $:alnum/'')) using $:utf8.
    sexp = $:alnum | list.
    list = "(" & sexp/nil/pair → L & ")" & L.
    head(pair(A, B)) = A.
    tail(pair(A, B)) = B.
    cons(A, B) = return pair(A, B).
    eval(pair(head, pair(X, nil))) = eval(X) → R & head(R).
    eval(pair(tail, pair(X, nil))) = eval(X) → R & tail(R).
    eval(pair(cons, pair(A, pair(B, nil)))) =
       eval(A) → AE & eval(B) → BE & return pair(AE, BE).
    eval(X) = X.
    reverse(pair(H, T), A) = reverse(H, nil) → HR & reverse(T, pair(HR, A)).
    reverse(nil, A) = A.
    reverse(X, A) = X.

Interpret a small subset of Tamsin in
**[30 lines of code](mains/micro-tamsin.tamsin)**
(not counting the [included batteries](doc/Philosophy.markdown#batteries-included).)

Compile Tamsin to C in
**[563 lines of code](mains/compiler.tamsin)**
(again, not counting the included batteries.)

For more information
--------------------

If the above has piqued your curiosity, you may want to read the specification,
which contains many more small examples written to demonstrate (and test) the
syntax and behavior of Tamsin:

*   [The Tamsin Language Specification](doc/Tamsin.markdown)

Note that this is the current development version of the specification, and
it may differ from the examples in this document.

Quick Start
-----------

The Tamsin reference repository is [hosted on Codeberg](https://codeberg.org/catseye/Tamsin).

This repository contains the reference implementation of Tamsin, called
`tamsin`, written in Python 2.7.  It can both interpret a Tamsin program and
compile a program written in Tamsin to C.

The distribution also contains a Tamsin-to-C compiler written in Tamsin.  It
passes all the tests, and can compile itself.

While the interpreter is fine for prototyping, note that some informal
benchmarking revealed the compiled C programs to be about 30x faster.  **Note**
however that while the compiler passes all the tests, it is still largely
unproven (e.g. its UTF-8 support is not RFC 3629-compliant), so it should be
considered a **proof of concept**.

To start using `tamsin`,

*   Clone the repository — `git clone https://codeberg.org/catseye/Tamsin`
*   Either:
    *   Put the repo's `bin` directory on your `$PATH`, or
    *   Make a symbolic link to `bin/tamsin` somewhere already on your `$PATH`.
*   Errr... that's it.

Then you can run `tamsin` like so:

*   `tamsin eg/csv_parse.tamsin < eg/names.csv`

To use the compiler, you'll need GNU make and `gcc` installed.  Type

*   `make`

to build the runtime library.  You can then compile to C and compile the C to
an executable and run the executable all in one step, like so:

*   `tamsin loadngo eg/csv_extract.tamsin < eg/names.csv`

Design Goals
------------

*   Allow parsers, static analyzers, interpreters, and compilers to be
    quickly prototyped.  (And in the future, processor simulators and VM's
    and such things too.)
*   Allow writing these things very compactly.
*   Allow writing anything using only recursive-descent parsing techniques
    (insofar as this is possible.)
*   Allow writing parsers that look very similar to the grammar of the
    language being parsed, so that the structure of the language can be
    clearly seen.
*   Provide means to solve practical problems.
*   Keep the language simple — the grammar should fit on a page, ideally.
*   Recognize that the preceding two goals are in tension.
*   Have a relatively simple reference implementation (currently less than
    5 KLoC, including everything — debugging support and the C runtime
    used by the compiler and the Tamsin modules and implementations.)

License
-------

BSD-style license; see the file [LICENSE](LICENSE).

Related work
------------

*   [CoCo/R](http://www.scifac.ru.ac.za/coco/) (parser generation)
*   [Parsec](http://www.haskell.org/haskellwiki/Parsec) (parser combinators)
*   [Perl](http://perl.org/) (rubbish listing)
*   [Prolog](https://en.wikipedia.org/wiki/Prolog) (pattern-matching, terms,
    backtracking(-ish...))
*   [K](https://github.com/kevinlawler/kona) (similar feel; Tamsin
    is a _vertical language_)
*   [Cat's Eye Technologies](http://catseye.tc)' esoteric and experimental
    languages:
    *   [Squishy2K](http://catseye.tc/node/Squishy2K)
    *   [Arboretuum](http://catseye.tc/node/Arboretuum)
    *   [Treacle](http://catseye.tc/node/Treacle)
