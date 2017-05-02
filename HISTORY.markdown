Tamsin Release History
======================

0.5-2017.0502
-------------

This is an interim release, created because the tests pass here, even
though not everything aimed for for the next release has been achieved.

### language ###

*   The RHS of → can be a pattern term.
*   "Proper quoted" strings.

### implementations ###

*   `mini-tamsin.tamsin` is an interpreter for "Mini-Tamsin", written in Tamsin.
*   Better error reporting.
*   Improvements or bugfixes in the C-language implementation of `$:unquote`.
*   Tamsin programs can handle streams on input and produce streams on output.
*   Begun work on a better C-emitting backend.
*   Better scanning; buffers are more sophisticated and track some state themselves.

0.5
---

### language ###

*   EOF is no longer a special kind of term; it is no longer exposed, as
    a value, to Tamsin programs.  (`$:eof` returns `''` on success.)
*   Prolog/Erlang-style list sugar for terms, in patterns as well.
*   When a new scanner is switched to using `using`, that scanner defaults
    to the `$:utf8` scanner for *its* scanning.  This prevents the common
    shooting-self-in-foot error of selecting a production that is not
    itself `using` another scanner (which would result in an infinite loop
    of the production scanner trying to use itself as its subsidiary
    scanner.)

### implementation ###

*   `struct term *`s are (almost) always `const` in compiled Tamsin
    programs (for better sharing; we don't need to make copies of them)
*   related: variable-matching is more efficient (directly updates an array
    of terms, instead of searching for the variable by name)
*   related: creating new atoms uses hash-consing, so that no new
    `struct term` for the atom is allocated if one already exists (the
    existing one is shared.)  This reduces memory usage significantly.

0.4
---

### language ###

*   Added `@` (work on different implicit buffer.)

### modules ###

*   Added `$:gensym`.
*   Added `$:hexchar`.
*   Added `$:format_octal`.
*   Added `$:length`.
*   Added `list:append`.

### implementations ###

*   Tamsin-to-C compiler written in Tamsin (`mains/compiler.tamsin`) passes
    all tests, and can compile itself.
*   Refactored `$` functions into `tamsin.sysmod` module in Python version.

0.3
---

### language ###

*   Defined what it means to `reprify` a term.
*   Clarified some matters as implementation-defined.

### modules ###

*   `$:equal` now does deep equality of arbitrary ground terms.
*   `$:repr` added.
*   `$:reverse` added.
*   Some standard modules ship in the distribution: `list`,
    `tamsin_scanner`, and `tamsin_parser`.

### implementations ###

*   Support for user-defined modules.
*   `tamsin` can take more than one source file on command line; this
    is how external modules are supported (by this implementation.)
*   Cleaned-up testing framework; Tamsin versions of scanner, grammar,
    parser, desugarer, analyzer, and compiler found in `mains` subdir.
*   Most `tamsin` verbs, and their versions in Tamsin, corresponding to
    intermediate phases, output reprified terms.
*   `tamsin` significantly re-factored so that the interpreter and
    compiler are more similar, and generating code for production branches
    is easier.
*   Added Tamsin-to-C compiler written in Tamsin, which can pass the first
    43 or so tests from the spec ("Mini-Tamsin").

0.2
---

### language ###

*   Module-member syntax changed from `.` to `:`.
*   `:` can be used without any module on the LHS to refer to a production
    in the current module.
*   Added "fold" forms, binary `/` and ternary `//`.

### modules ###

*   `$:char` scanner dropped.  Instead, there are `$:byte` (which always
    returns 8-bit-clean bytes) and `$:utf8` (which always returns UTF-8
    sequences.)
*   Added `$:equal(L,R)`.
*   `$:unquote(X,L,R)` takes three arguments now.

### implementations ###

*   Beginnings of user-defined module support (very rudimentary, not to be
    used.)
*   Code in `libtamsin` is much more robust.  AST-builder written in Tamsin now
    compiles and runs correctly.
*   Added a desugaring phase to `tamsin`, and a desugarer written in Tamsin.
*   Added Micro-Tamsin interpreter, written in Tamsin.  Can pass the first
    30 tests from the spec.

0.1
---

Initial release.
